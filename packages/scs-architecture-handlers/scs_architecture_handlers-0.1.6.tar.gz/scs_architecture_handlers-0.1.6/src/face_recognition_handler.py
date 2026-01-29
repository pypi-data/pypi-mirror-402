"""FaceRecognitionHandler that calls our external FastAPI server.

Run this file directly to see the handler process a dummy frame. If no API
configuration is provided, it runs in dry-run mode and returns a stub result.
"""
from __future__ import annotations

import io
import os
import time
import threading
import queue
from typing import Any, Dict, Callable, Optional

import numpy as np
import requests
from PIL import Image

from base_handler import ArchitectureHandler


class FaceRecognitionHandler(ArchitectureHandler):
    """Handler that posts frames to a remote /detect endpoint.

    Parameters (in addition to base ArchitectureHandler):
    - api_key: Optional[str]     API key for the x-api-key header
    - process_stream: str        Value for the process-stream header (defaults to "default_stream")
    - dry_run: bool              If True, skip network call and return a stub result

    Webcam mode (optional):
    - auto_webcam: bool                  If True, open the default webcam and feed frames automatically
    - webcam_index: int                  cv2.VideoCapture index (default 0)
    - webcam_fps: Optional[float]        Target capture FPS. If None, capture as fast as possible.
    - webcam_queue_size: int             Max pending frames to process (forced to 1 to avoid wasted work)
    - callback_queue_size: int           Max pending callback tasks (forced to 1, latest-result-wins)

    Notes
    -----
    When auto_webcam is enabled:
    - frames are produced on a dedicated thread
    - input queue is effectively bounded to size 1 (latest-frame-wins)
    - generate_results_callback (if provided) is invoked on its own thread with the FINAL result
      (after postprocess_result), and the callback work queue is bounded to size 1
    """

    REQUIRED_KEYS = {"frame", "timestamp"}

    def __init__(
        self,
        *,
        host: str,
        port: int,
        api_key: str,
        process_stream: str = "default_stream",
        dry_run: bool = False,
        # Webcam mode
        auto_webcam: bool = False,
        webcam_index: int = 0,
        webcam_fps: Optional[float] = None,
        webcam_queue_size: int = 1,
        callback_queue_size: int = 1,
        webcam_frame_provider: Optional[Callable[[], Optional[np.ndarray]]] = None,
        # Base parameters

        auth: Any = None,
        run_as_thread: bool = True,
        disable_thread: bool = False,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        expected_type: Optional[type] = None,
        network_timeout: Optional[float] = 10.0,
        client_id_prefix: str = "client",
        generate_results_callback: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,  # type: ignore[name-defined]
    ):

        super().__init__(
            host=host,
            port=port,
            auth=auth,
            run_as_thread=False, # we start this manually at the end of __init__
            disable_thread=disable_thread,
            max_queue_size=max_queue_size,
            result_queue_size=result_queue_size,
            verbose=verbose,
            expected_type=expected_type,
            network_timeout=network_timeout,
            client_id_prefix=client_id_prefix,
            generate_results_callback=generate_results_callback,
            callback_queue_size=max(1, int(callback_queue_size)),
        )

        # API config
        self.api_key: Optional[str] = api_key
        self.process_stream: str = process_stream
        self.dry_run: bool = bool(dry_run)
        # Default timeout for requests
        self._timeout: float = float(self.network_timeout or 10.0)

        # Webcam / callback threading config
        self.auto_webcam: bool = bool(auto_webcam)
        self.webcam_index: int = int(webcam_index)
        self.webcam_fps: Optional[float] = float(webcam_fps) if webcam_fps is not None else None
        # Force maxsize 1 semantics (avoid resource waste)
        self.webcam_queue_size: int = 1 if self.auto_webcam else max(1, int(webcam_queue_size))
        self._callback_task_queue_maxsize: int = 1 if self.auto_webcam else max(1, int(callback_queue_size))

        # Optional injection for tests (avoids needing cv2 / real webcam)
        self._webcam_frame_provider: Optional[Callable[[], Optional[np.ndarray]]] = webcam_frame_provider

        # Threads/queues used only in webcam mode
        self._webcam_thread: Optional[threading.Thread] = None
        self._callback_result_thread: Optional[threading.Thread] = None
        self._callback_result_queue: "queue.Queue[tuple[Any, Dict[str, Any]]]" = queue.Queue(
            maxsize=self._callback_task_queue_maxsize
        )

        # Light instrumentation for webcam mode (in addition to base counters)
        self.webcam_frame_count: int = 0
        self.webcam_drop_count: int = 0
        self.webcam_callback_drop_count: int = 0

        if self.auto_webcam:
            # Replace input queue with size 1 queue (latest-frame-wins). We keep result_queue
            # unchanged by default so get_result() still works.
            self.input_queue = queue.Queue(maxsize=1)

        # Now start threads if requested
        if run_as_thread and not disable_thread:
            self.start()



    # --- Validation / Preprocess ---
    def validate_item(self, item: Dict[str, Any], extra: Dict[str, Any]) -> bool:  # type: ignore[override]
        if not isinstance(item, dict):
            return False
        if not self.REQUIRED_KEYS.issubset(item.keys()):
            return False
        frame = item.get("frame")
        if not isinstance(frame, np.ndarray) or frame.ndim != 3:
            return False
        return True

    def preprocess_item(self, item: Dict[str, Any], extra: Dict[str, Any]):  # type: ignore[override]
        # Ensure the frame is uint8 for JPEG encoding
        frame = item["frame"]
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        return {**item, "frame": frame}, extra

    # --- Core generation ---
    def generate_results(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Any:  # type: ignore[override]
        # Build payload for network request (image bytes + headers)
        payload = self._prepare_request_payload(item, extra)
        response = self.perform_request(payload)
        return response

    def postprocess_result(self, item: Dict[str, Any], extra: Dict[str, Any], result: Any) -> Any:  # type: ignore[override]
        # Attach original timestamp for downstream consumers
        if isinstance(result, dict):
            result = {**result, "ts": item["timestamp"]}

        # In webcam mode, always run generate_results_callback on a dedicated thread.
        # We treat it as a *result sink* rather than the core generator.
        if self.auto_webcam and self._external_callback is not None:
            self._emit_result_callback(result, {"item": item, **(extra or {})})
        return result

    # --- Webcam + callback threads ---
    def start(self) -> None:  # type: ignore[override]
        # Start base processing thread(s)
        super().start()

        if not self.auto_webcam or self.disable_thread:
            return

        if self._webcam_thread is None or not self._webcam_thread.is_alive():
            self._webcam_thread = threading.Thread(
                target=self._webcam_loop,
                name=f"Webcam-{self.client_id}",
                daemon=True,
            )
            self._webcam_thread.start()

        # Ensure result-callback thread is up if callback exists
        if self._external_callback and (self._callback_result_thread is None or not self._callback_result_thread.is_alive()):
            self._callback_result_thread = threading.Thread(
                target=self._result_callback_loop,
                name=f"ResultCallback-{self.client_id}",
                daemon=True,
            )
            self._callback_result_thread.start()

    def cleanup(self) -> None:  # type: ignore[override]
        super().cleanup()

        # Join webcam/callback threads (best effort)
        if self._webcam_thread:
            try:
                self._webcam_thread.join(timeout=2)
            except Exception:
                pass
        if self._callback_result_thread:
            try:
                self._callback_result_thread.join(timeout=2)
            except Exception:
                pass

    def _put_latest_nowait(self, q: "queue.Queue[Any]", value: Any, *, drop_counter_attr: Optional[str] = None) -> bool:
        """Put without blocking; if queue is full, drop one old item and retry once."""
        try:
            q.put(value, block=False)
            return True
        except queue.Full:
            try:
                q.get_nowait()
                q.task_done()
            except Exception:
                # If we can't pop, we drop new work
                if drop_counter_attr is not None:
                    setattr(self, drop_counter_attr, getattr(self, drop_counter_attr, 0) + 1)
                self.dropped_count += 1
                return False

            if drop_counter_attr is not None:
                setattr(self, drop_counter_attr, getattr(self, drop_counter_attr, 0) + 1)
            self.dropped_count += 1
            try:
                q.put(value, block=False)
                return True
            except queue.Full:
                if drop_counter_attr is not None:
                    setattr(self, drop_counter_attr, getattr(self, drop_counter_attr, 0) + 1)
                self.dropped_count += 1
                return False

    def _emit_result_callback(self, result: Any, extra: Dict[str, Any]) -> bool:
        if self._external_callback is None:
            return False
        # Ensure callback thread exists
        if not self.disable_thread and (self._callback_result_thread is None or not self._callback_result_thread.is_alive()):
            self._callback_result_thread = threading.Thread(
                target=self._result_callback_loop,
                name=f"ResultCallback-{self.client_id}",
                daemon=True,
            )
            self._callback_result_thread.start()
        return self._put_latest_nowait(self._callback_result_queue, (result, dict(extra)), drop_counter_attr="webcam_callback_drop_count")

    def _result_callback_loop(self) -> None:
        while not self.stop_event.is_set() or not self._callback_result_queue.empty():
            try:
                result, extra = self._callback_result_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                # Callback signature is user-defined; we pass result as item
                self._external_callback(result, extra)  # type: ignore[misc]
            except Exception as exc:
                try:
                    self._hook_on_error(result, extra, exc)
                except Exception:
                    self._logger.exception("Error in _hook_on_error (from result callback)")
            finally:
                try:
                    self._callback_result_queue.task_done()
                except Exception:
                    pass

    def _webcam_loop(self) -> None:
        """Capture loop.

        Uses either an injected frame provider (tests) or OpenCV when available.
        Feeds frames into the handler via the maxsize-1 input queue (latest-frame-wins).
        """
        cap = None
        provider = self._webcam_frame_provider
        if provider is None:
            try:
                import cv2  # type: ignore

                cap = cv2.VideoCapture(self.webcam_index)

                def _cv2_provider() -> Optional[np.ndarray]:
                    if cap is None or not cap.isOpened():
                        return None
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        return None
                    # cv2 gives BGR; most pipelines expect RGB, but we keep as-is
                    return frame

                provider = _cv2_provider
            except Exception as exc:
                self._logger.warning("Webcam mode requested but OpenCV is unavailable: %s", exc)
                return

        period = None
        if self.webcam_fps is not None and self.webcam_fps > 0:
            period = 1.0 / float(self.webcam_fps)

        next_deadline = time.monotonic()

        try:
            while not self.stop_event.is_set():
                if period is not None:
                    now = time.monotonic()
                    sleep_s = next_deadline - now
                    if sleep_s > 0:
                        time.sleep(sleep_s)
                    # Schedule next capture time (avoids drift)
                    next_deadline = max(next_deadline + period, time.monotonic())

                frame = provider() if provider is not None else None
                if frame is None:
                    time.sleep(0.02)
                    continue

                self.webcam_frame_count += 1
                item = {"frame": frame, "timestamp": time.time()}

                # Validate before enqueue to avoid wasting queue slots
                if not self.validate_item(item, {}):
                    continue

                # Enqueue latest-frame (queue size is 1). We bypass feed() to implement drop policy.
                self._put_latest_nowait(self.input_queue, (item, {}), drop_counter_attr="webcam_drop_count")
        finally:
            try:
                if cap is not None:
                    cap.release()
            except Exception:
                pass

    # --- Networking helpers ---
    def _prepare_request_payload(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        frame: np.ndarray = item["frame"]
        # Convert numpy array (H, W, C) to JPEG bytes via PIL
        image = Image.fromarray(frame)
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=90)
        img_bytes = buf.getvalue()
        buf.close()

        return {
            "client_id": self.client_id,
            "image_bytes": img_bytes,
            "filename": f"frame_{int(time.time()*1000)}.jpg",
            "content_type": "image/jpeg",
            "headers": {
                # FastAPI converts underscores to hyphens for headers
                "x-api-key": self.api_key or "",
                "process-stream": self.process_stream,
            },
            "url": self._detect_url(),
            "timeout": self._timeout,
        }

    def _perform_request(self, payload: Dict[str, Any]):  # type: ignore[override]
        # In dry-run, return a stubbed result without network I/O
        if self.dry_run or not payload.get("url"):
            print("[FaceRecognitionHandler] Dry run mode or missing config; skipping network request.")
            print(f"  dry_run: {self.dry_run}, url: {payload.get('url')}, api_key: {'set' if self.api_key else 'unset'}")
            # Minimal plausible structure to aid local testing
            return {
                "detectedPersons": [],
                "numPersons": 0,
                "fps": 0.0,
            }

        url = payload["url"]
        headers = payload.get("headers", {})
        files = {
            "file": (
                payload.get("filename", "frame.jpg"),
                payload["image_bytes"],
                payload.get("content_type", "application/octet-stream"),
            ),
        }
        timeout = payload.get("timeout", self._timeout)

        try:
            resp = requests.post(url, headers=headers, files=files, timeout=timeout)
            resp.raise_for_status()
            print(resp.status_code)
        except requests.exceptions.RequestException as exc:
            msg = f"[FaceRecognitionHandler] ERROR: Could not connect to server at {url}: {exc}"
            if hasattr(exc, 'response') and exc.response is not None:
                status = exc.response.status_code
                if status == 401 or status == 403:
                    msg += " (API key invalid or unauthorized)"
            self._logger.error(msg)
            return {"error": msg, "detectedPersons": [], "numPersons": 0, "fps": 0.0}
        except Exception as exc:
            msg = f"[FaceRecognitionHandler] ERROR: Unexpected error during request: {exc}"
            self._logger.error(msg)
            return {"error": msg, "detectedPersons": [], "numPersons": 0, "fps": 0.0}
        # Expect JSON with keys: detectedPersons, numPersons, fps
        return resp.json()

    # --- URL helpers ---
    def _detect_url(self) -> Optional[str]:
        if not (self.host and self.port):
            return None
        base = f"http://{self.host}:{self.port}"
        return f"{base}/detect"


def _demo():
    # Read environment for convenience
    process_stream = os.getenv("FR_PROCESS_STREAM", "default_stream")

    # Enable dry_run
    dry_run = True

    handler = FaceRecognitionHandler(
        host="localhost",
        port=42001,
        api_key="16514931512135059181828385281700",
        process_stream=process_stream,
        dry_run=dry_run,
        run_as_thread=True,
        verbose=True,
        network_timeout=10.0,
    )

    # Create a dummy frame
    frame = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    handler.feed({"frame": frame, "timestamp": time.time()})
    result = handler.get_result(timeout=5.0)
    print("Result:", result)
    print("Stats:", handler.stats())
    handler.cleanup()


def _demo_auto_webcam():
    """Demo for auto_webcam mode using a dummy frame provider (no real webcam required)."""
    import threading
    import numpy as np
    import time

    callback_results = []
    callback_event = threading.Event()
    def on_result(result, extra):
        print(f"[CALLBACK] Got result: {result}")
        callback_results.append(result)
        callback_event.set()

    handler = FaceRecognitionHandler(
        host="localhost",
        port=42001,
        api_key="16514931512135059181828385281700",
        auto_webcam=True,
        webcam_fps=5.0,
        #webcam_frame_provider=provider,
        dry_run=False,
        run_as_thread=True,
        generate_results_callback=on_result,
        verbose=True,
    )
    print("[DEMO] Started auto_webcam handler")
    # Wait for at least one callback
    callback_event.wait(timeout=2.0)
    # Wait for all frames to be processed
    time.sleep(1.5)
    print(f"[DEMO] Processed {len(callback_results)} results. Stats: {handler.webcam_frame_count} frames, {handler.webcam_drop_count} dropped.")
    handler.cleanup()


if __name__ == "__main__":
    _demo_auto_webcam()
    #_demo()
