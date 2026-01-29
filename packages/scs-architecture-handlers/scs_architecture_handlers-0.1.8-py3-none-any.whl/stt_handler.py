from __future__ import annotations

import time
import traceback
from typing import Any, Dict, Optional

from base_handler import ArchitectureHandler


class STTHandler(ArchitectureHandler):
    """Speech-to-Text handler that continuously pulls microphone audio using
    RealtimeSTT.AudioToTextRecorderClient and emits recognized text results.

    This handler doesn't require feed(); instead, it owns the microphone and
    produces results on its own thread. Consumers can either:
      - Provide an external callback (generate_results_callback) to receive
        results as they arrive, or
      - Call get_result() to pull the oldest result from the queue.

    Result shape pushed to the queue / callback:
      { "type": "audio", "data": <str>, "ts": <float>, "client_id": <str> }

    Parameters (subset):
      - control_url: str  (websocket control URL for RealtimeSTT)
      - data_url: str     (websocket data URL for RealtimeSTT)
      - language: str     (e.g., "de")
      - silero_sensitivity: float
      - use_microphone: bool
      - input_device_index: Optional[int]
      - poll_interval: float seconds between polls if no text available
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        control_url: str,
        data_url: str,
        language: str = "de",
        silero_sensitivity: float = 0.1,
        use_microphone: bool = True,
        input_device_index: Optional[int] = None,
        poll_interval: float = 0.01,
        # Base parameters
        run_as_thread: bool = True,
        disable_thread: bool = False,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        network_timeout: Optional[float] = None,
        client_id_prefix: str = "client",
        generate_results_callback: Optional[Any] = None,
        callback_queue_size: int = 128,
    ) -> None:
        # Defer auto-thread start until after we set our fields to avoid race conditions
        requested_thread = run_as_thread
        super().__init__(
            host=None,
            port=None,
            auth=None,
            run_as_thread=False,  # prevent auto-start here
            disable_thread=disable_thread,
            max_queue_size=max_queue_size,
            result_queue_size=result_queue_size,
            verbose=verbose,
            expected_type=None,
            network_timeout=network_timeout,
            client_id_prefix=client_id_prefix,
            generate_results_callback=generate_results_callback,
            callback_queue_size=callback_queue_size,
        )
        self.control_url = control_url
        self.data_url = data_url
        self.language = language
        self.silero_sensitivity = float(silero_sensitivity)
        self.use_microphone = bool(use_microphone)
        self.input_device_index = input_device_index
        self.poll_interval = float(poll_interval)
        # These are initialized in the processing loop
        self._stt_client = None
        self.api_key = api_key
        # Now start threads if requested
        if requested_thread and not disable_thread:
            self.start()

    # We don't expect external feed; guard against misuse
    def feed(self, item: Any, **extra: Any) -> bool:  # type: ignore[override]
        self._logger.warning("STTHandler ignores feed(); it's a self-producing handler.")
        try:
            self._hook_after_feed(item, dict(extra), False)
        except Exception:
            self._logger.exception("Error in _hook_after_feed")
        return False

    # Core processing loop override
    def _processing_loop(self) -> None:  # type: ignore[override]
        # Lazy imports to avoid hard dependencies at import time
        try:
            from RealtimeSTT import AudioToTextRecorderClient  # type: ignore
        except Exception as exc:
            self._logger.exception("RealtimeSTT import failed: %s", exc)
            try:
                self._hook_on_error(None, {}, exc)
            except Exception:
                self._logger.exception("Error in _hook_on_error")
            # Nothing to do without the dependency; stop.
            self.stop_event.set()
            return

        # Determine input device if not provided (best-effort; optional)
        device_index = self.input_device_index
        if device_index is None and self.use_microphone:
            try:
                import pyaudio  # type: ignore
                p = pyaudio.PyAudio()
                info = p.get_host_api_info_by_index(0)
                numdevices = info.get("deviceCount", 0)
                for i in range(0, int(numdevices)):
                    dev = p.get_device_info_by_host_api_device_index(0, i)
                    if dev.get("maxInputChannels", 0) > 0:
                        name = (dev.get("name") or "").lower()
                        if "default" in name:
                            print(f"Selecting default input device: {name} (index {i})")
                            device_index = i
                            break

                try:
                    p.terminate()
                except Exception:
                    pass
            except Exception:
                # If PyAudio not available, proceed without selecting device
                device_index = None

        # Initialize the STT client
        try:
            self._stt_client = AudioToTextRecorderClient(
                api_key=self.api_key,
                language=self.language,
                control_url=self.control_url,
                data_url=self.data_url,
                debug_mode=False,
                silero_sensitivity=self.silero_sensitivity,
                use_microphone=self.use_microphone,
                input_device_index=device_index,
                autostart_server=False,
            )
        except Exception as exc:
            # This commonly happens if the websocket server is unreachable.
            self._logger.warning(
                "STTHandler failed to initialize STT client (server unreachable?). "
                "Stopping handler. control_url=%s data_url=%s error=%r",
                self.control_url,
                self.data_url,
                exc,
            )
            self._logger.debug("Initialize exception traceback:")
            self._logger.debug("%s", traceback.format_exc())
            try:
                self._hook_on_error(None, {}, exc)
            except Exception:
                self._logger.exception("Error in _hook_on_error")
            self.stop_event.set()
            return
        print("STTHandler connected to RealtimeSTT server.")
        # Main poll loop
        while not self.stop_event.is_set():
            try:
                text = self._stt_client.text()

                # RealtimeSTT may return (text, meta) or just text. Normalize.
                meta = None
                if isinstance(text, tuple) and len(text) == 2:
                    text, meta = text

                if isinstance(text, str) and text.strip():
                    result = {
                        "type": "audio",
                        "data": text,
                        "ts": time.time(),
                        "client_id": self.client_id,
                    }
                    # Schedule external callback asynchronously (non-blocking)
                    self._emit_async_callback(result, {})
                    # Attempt to enqueue without blocking
                    try:
                        self.result_queue.put(result, block=False)
                    except Exception:
                        self.dropped_count += 1
                    try:
                        # Update timestamps and counters similarly to generate path
                        self._hook_after_generate(None, {}, result)
                    except Exception:
                        self._logger.exception("Error in _hook_after_generate")
                else:
                    # Backoff a bit if no new text
                    time.sleep(self.poll_interval)
            except Exception as exc:
                # If polling fails (e.g., websocket disconnect), stop instead of looping forever.
                self._logger.warning(
                    "STTHandler lost connection / failed while polling. Stopping handler. error=%r",
                    exc,
                )
                self._logger.debug("Polling exception traceback:")
                self._logger.debug("%s", traceback.format_exc())
                try:
                    self._hook_on_error(None, {}, exc)
                except Exception:
                    self._logger.exception("Error in _hook_on_error")
                self.stop_event.set()
                break

        # Teardown
        try:
            if self._stt_client is not None:
                # Best-effort close if available
                close_fn = getattr(self._stt_client, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        traceback.print_exc()
        finally:
            self._stt_client = None

