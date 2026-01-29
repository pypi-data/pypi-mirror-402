from __future__ import annotations

import json
import logging
import queue
import threading
import time
import wave
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

from base_handler import ArchitectureHandler
from f5tts_handler import F5TTSHandler
from gesture_generation_handler import GestureGenerationHandler
from gesture_generation_helper import to_frame_string


@dataclass(frozen=True)
class VisualizerConfig:
    """Connection config for the external visualizer (Unity websocket)."""

    url: str = "ws://127.0.0.1:1338/Animate"
    look_target_move_speed: float = 0.4


class VisualizerConnectionError(RuntimeError):
    pass


class MaverickAgentHandler(ArchitectureHandler):
    """Orchestrates realtime gesture streaming + agent TTS playback.

    This handler mimics the behavior of your original `inference.py` loop:
      - It maintains a continuous stream to the external visualizer.
      - When no audio is available, it keeps sending small "noise" chunks so the
        gesture model keeps producing realtime output.
      - When the agent responds, call `send_agent_text(text)` (or feed an item)
        to synthesize audio (F5-TTS), chunk it, run gesture generation per chunk,
        and stream (gesture+audio) frames to the visualizer.

    Input item schema (for generate/feed):
      {"kind": "agent_text", "text": str}

    Result schema:
      {"status": "queued", "text": str, "ts": float}

    Notes
    -----
    - Uses `websocket-client` (imported lazily) like the original.
    - Uses GestureGenerationHandler to call your realtimebeatgesture FastAPI.
    - Uses F5TTSHandler to call your F5-TTS FastAPI.
    """

    def __init__(
        self,
        *,
        # visualizer
        visualizer: VisualizerConfig = VisualizerConfig(),
        # gesture generation API
        gesture_host: Optional[str] = None,
        gesture_port: Optional[int] = None,
        gesture_api_key: Optional[str] = None,
        gesture_timeout: float = 10.0,
        # tts API
        tts_host: Optional[str] = None,
        tts_port: Optional[int] = None,
        tts_api_key: Optional[str] = None,
        tts_timeout: float = 60.0,
        # tts content
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        # streaming params
        sample_rate: int = 24000,
        fps: int = 30,
        n_frames: int = 2,
        idle_noise_amplitude: float = 0.0,
        idle_dither: float = 1e-4,
        # base
        run_as_thread: bool = True,
        disable_thread: bool = False,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        expected_type: Optional[type] = None,
    ) -> None:
        super().__init__(
            host=None,
            port=None,
            auth=None,
            run_as_thread=run_as_thread,
            disable_thread=disable_thread,
            max_queue_size=max_queue_size,
            result_queue_size=result_queue_size,
            verbose=verbose,
            expected_type=expected_type,
            network_timeout=None,
            client_id_prefix="maverick",
            generate_results_callback=None,
        )

        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(logging.INFO if verbose else logging.WARNING)

        self.visualizer = visualizer

        self.sample_rate = int(sample_rate)
        self.fps = int(fps)
        self.n_frames = int(n_frames)
        if self.sample_rate <= 0 or self.fps <= 0 or self.n_frames <= 0:
            raise ValueError("sample_rate, fps, n_frames must be positive")

        self.chunk_size = int(self.n_frames * (self.sample_rate / self.fps))
        if self.chunk_size <= 0:
            raise ValueError("Invalid chunk_size computed")

        self.idle_noise_amplitude = float(idle_noise_amplitude)
        self.idle_dither = float(idle_dither)

        if reference_audio is None:
            raise ValueError(
                "reference_audio must be provided (path to speaker reference wav/mp3) "
                "for F5-TTS synthesis."
            )
        self.reference_audio = reference_audio
        self.reference_text = reference_text

        # Sub-handlers (sync usage)
        self.gesture_handler = GestureGenerationHandler(
            host=gesture_host,
            port=gesture_port,
            api_key=gesture_api_key,
            dry_run=False,
            run_as_thread=False,
            disable_thread=True,
            verbose=verbose,
            network_timeout=float(gesture_timeout),
        )
        self.tts_handler = F5TTSHandler(
            host=tts_host,
            port=tts_port,
            api_key=tts_api_key,
            dry_run=False,
            run_as_thread=False,
            disable_thread=True,
            verbose=verbose,
            network_timeout=float(tts_timeout),
        )

        # Internal queues
        self._audio_queue: "queue.Queue[Tuple[np.ndarray, bool]]" = queue.Queue(maxsize=256)
        self._ws_send_queue: "queue.Queue[Tuple[str, str]]" = queue.Queue(maxsize=256)
        self._stop_streaming = threading.Event()

        # Background threads
        self._stream_thread: Optional[threading.Thread] = None
        self._ws_thread: Optional[threading.Thread] = None

        # Start background worker threads if configured.
        # Important: threads should NOT start until we have valid connectivity (demo calls assert_ready()).
        # Users of the class can still call start_streaming() explicitly after setting keys/hosts.
        if self.run_as_thread and not self.disable_thread:
            # Do not auto-start here; avoid spamming connection errors on misconfig.
            pass

    def start_streaming(self) -> None:
        """Start streaming threads (visualizer websocket + gesture loop)."""
        if self._stream_thread and self._stream_thread.is_alive():
            return
        self._start_streaming_threads()

    # ----- Public API -----
    def send_agent_text(self, text: str) -> Dict[str, Any]:
        """Queue TTS+gesture streaming for the agent response."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        item = {"kind": "agent_text", "text": text.strip()}
        return self.generate(item)

    # ArchitectureHandler overrides
    def validate_item(self, item: Any, extra: Dict[str, Any]) -> bool:  # type: ignore[override]
        if not isinstance(item, dict):
            return False
        if item.get("kind") != "agent_text":
            return False
        return isinstance(item.get("text"), str) and bool(item.get("text").strip())

    def generate_results(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Any:  # type: ignore[override]
        # Synthesize audio now (blocking), then enqueue chunks for streaming.
        text = item["text"].strip()
        audio = self._synthesize_text_to_audio(text)
        self._enqueue_audio_chunks(audio, speaking=True)
        return {"status": "queued", "text": text, "ts": time.time()}

    def cleanup(self) -> None:  # type: ignore[override]
        # Stop base threads
        try:
            super().cleanup()
        finally:
            # Stop our streaming threads
            self._stop_streaming.set()
            self._stop_streaming_threads()

    # ----- Streaming / Connection management -----
    def _start_streaming_threads(self) -> None:
        if self._stream_thread and self._stream_thread.is_alive():
            return
        self._stop_streaming.clear()
        self._ws_thread = threading.Thread(target=self._visualizer_ws_loop, name="Maverick-WS", daemon=True)
        self._ws_thread.start()
        self._stream_thread = threading.Thread(target=self._gesture_stream_loop, name="Maverick-Stream", daemon=True)
        self._stream_thread.start()

    def _stop_streaming_threads(self) -> None:
        for th in (self._stream_thread, self._ws_thread):
            if th is not None:
                try:
                    th.join(timeout=2)
                except Exception:
                    pass

    def _visualizer_ws_loop(self) -> None:
        """Maintains a connection to the external visualizer and sends payloads."""
        try:
            import websocket  # websocket-client
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency 'websocket-client'. Install it to stream to the visualizer."
            ) from exc

        ws = None
        last_err_log = 0.0

        while not self._stop_streaming.is_set():
            try:
                if ws is None:
                    ws = websocket.create_connection(self.visualizer.url, timeout=5)

                try:
                    frame_str, audio_str = self._ws_send_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                payload = {
                    "BVHData": frame_str,
                    "AudioData": str(audio_str),
                    "LookTarget": "0.0 0.0 0.0",
                    "LookTargetMoveSpeed": str(self.visualizer.look_target_move_speed),
                }
                ws.send(json.dumps(payload))
            except Exception as exc:
                # Reset connection and keep trying
                ws = None
                # Throttle logs to avoid spamming
                if time.time() - last_err_log > 2.0:
                    last_err_log = time.time()
                    self._log.error(
                        "Visualizer websocket connection failed (%s). Is the visualizer running at %s?",
                        exc,
                        self.visualizer.url,
                    )
                time.sleep(0.2)

        # best-effort close
        try:
            if ws is not None:
                ws.close()
        except Exception:
            pass

    def _gesture_stream_loop(self) -> None:
        """Continuously generates gestures from audio chunks and enqueues messages to send."""
        sleep_anchor = time.time()
        frame_period = self.n_frames / float(self.fps)

        while not self._stop_streaming.is_set():
            try:
                try:
                    audio_chunk, speaking = self._audio_queue.get_nowait()
                except queue.Empty:
                    audio_chunk = self._idle_audio_chunk()
                    speaking = False

                # Gesture inference via FastAPI handler
                item = {"audio": audio_chunk, "sample_rate": self.sample_rate, "timestamp": time.time()}
                gesture_out = self.gesture_handler.generate(item)

                if not isinstance(gesture_out, dict):
                    raise RuntimeError(f"Gesture handler returned non-dict: {type(gesture_out)}")

                # expected output from your python core: {frame_string or bones}
                frame_str = gesture_out.get("frame_string")
                if frame_str is None:
                    frame_str = to_frame_string(gesture_out["bones"],[0,1,2],[1,1,1])
                    # Some servers might return only bones; if so, fail loudly (we need frame string for the visualizer)
                    # raise RuntimeError(
                    #     "Gesture API response missing 'frame_string'. "
                    #     "Update gesture server to return it or adapt handler to compute it."
                    # )

                audio_str = " ".join(str(f) for f in audio_chunk.astype(np.float32).flatten())

                try:
                    self._ws_send_queue.put((frame_str, audio_str), block=False)
                except queue.Full:
                    # Backpressure: drop frames rather than blocking realtime loop
                    self._log.warning("Visualizer send queue full; dropping frame")

                # pacing like inference.py
                do_sleep = frame_period - (time.time() - sleep_anchor)
                if do_sleep > 0.0:
                    time.sleep(do_sleep)
                sleep_anchor = time.time()
            except Exception as exc:
                # Clear, actionable error for a likely misconfig
                self._log.error(
                    "Gesture streaming error: %s. Check gesture API host/port (%s:%s) and server logs.",
                    exc,
                    self.gesture_handler.host,
                    self.gesture_handler.port,
                )
                time.sleep(0.25)

    # ----- Audio synthesis / chunking -----
    def _synthesize_text_to_audio(self, text: str) -> np.ndarray:
        """Call F5TTS handler, decode wav bytes, return mono float32 array in [-1, 1]."""
        try:
            tts_out = self.tts_handler.generate_results(
                {
                    "text": text,
                    "reference_audio": self.reference_audio,
                    "reference_text": self.reference_text,
                },{}
            )
        except Exception as exc:
            raise RuntimeError(
                f"TTS synthesis failed: {exc}. Check F5-TTS server at {self.tts_handler.host}:{self.tts_handler.port}"
            ) from exc

        if not isinstance(tts_out, dict) or "audio_bytes" not in tts_out:
            raise RuntimeError(f"TTS handler returned unexpected output: {tts_out}")

        audio_bytes = tts_out["audio_bytes"]
        if not isinstance(audio_bytes, (bytes, bytearray)) or len(audio_bytes) < 16:
            raise RuntimeError("TTS returned empty/invalid audio bytes")

        # Decode PCM from WAV (standard library)
        try:
            with wave.open(io:=_BytesReader(audio_bytes), "rb") as wf:  # type: ignore[arg-type]
                sr = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                frames = wf.readframes(wf.getnframes())
        except Exception as exc:
            raise RuntimeError(
                "Failed to decode WAV from TTS. Ensure F5-TTS returns wav/pcm (not mp3/ogg)."
            ) from exc

        if sampwidth != 2:
            raise RuntimeError(f"Unsupported WAV sample width: {sampwidth * 8} bits; expected 16-bit PCM")

        pcm = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if n_channels > 1:
            pcm = pcm.reshape(-1, n_channels).mean(axis=1)

        if sr != self.sample_rate:
            # Avoid heavy deps: do a simple linear resample
            pcm = _resample_linear(pcm, sr, self.sample_rate)

        pcm = np.clip(pcm, -1.0, 1.0).astype(np.float32, copy=False)
        return pcm

    def _enqueue_audio_chunks(self, audio: np.ndarray, speaking: bool) -> None:
        if audio.ndim != 1:
            audio = audio.flatten()

        # Ensure at least one chunk
        if audio.size == 0:
            audio = np.zeros((self.chunk_size,), dtype=np.float32)

        # Pad to chunk boundary
        remainder = int(audio.size % self.chunk_size)
        if remainder:
            pad = self.chunk_size - remainder
            audio = np.pad(audio, (0, pad))

        for i in range(0, int(audio.size), self.chunk_size):
            chunk = audio[i : i + self.chunk_size]
            try:
                self._audio_queue.put((chunk.astype(np.float32, copy=False), speaking), timeout=2.0)
            except queue.Full:
                self._log.warning("Audio queue full; dropping remaining synthesized audio")
                break

    def _idle_audio_chunk(self) -> np.ndarray:
        # Inference.py adds a small dither; do similar but keep amplitude tiny.
        if self.idle_noise_amplitude > 0.0:
            noise = np.random.uniform(-1.0, 1.0, size=(self.chunk_size,)).astype(np.float32)
            noise *= self.idle_noise_amplitude
        else:
            noise = np.zeros((self.chunk_size,), dtype=np.float32)
        if self.idle_dither:
            noise += np.float32(np.random.uniform(-1.0, 1.0) * self.idle_dither)
        return np.clip(noise, -1.0, 1.0).astype(np.float32, copy=False)

    @classmethod
    def demo(
        cls,
        *,
        visualizer_url: str = "ws://127.0.0.1:1338/Animate",
        gesture_host: str = "127.0.0.1",
        gesture_port: int = 42005,
        tts_host: str = "127.0.0.1",
        tts_port: int = 42006,
        reference_audio: str,
        reference_text: Optional[str] = None,
        gesture_api_key: Optional[str] = None,
        tts_api_key: Optional[str] = None,
        sample_rate: int = 24000,
        fps: int = 30,
        n_frames: int = 2,
        gesture_timeout: float = 10.0,
        tts_timeout: float = 60.0,
        verbose: bool = True,
    ) -> None:
        """Run an interactive end-to-end demo.

        This is meant to be used with:
          - a running Unity visualizer at `visualizer_url`
          - a running realtimebeatgesture FastAPI at `gesture_host:gesture_port`
          - a running F5-TTS FastAPI at `tts_host:tts_port`

        It connects to all components, then prompts for text. Each line is sent
        through TTS -> chunking -> gesture generation -> websocket streaming.

        Exit with Ctrl+C or an empty line.
        """
        import os

        h = cls(
            visualizer=VisualizerConfig(url=visualizer_url),
            gesture_host=gesture_host,
            gesture_port=gesture_port,
            gesture_timeout=gesture_timeout,
            tts_host=tts_host,
            tts_port=tts_port,
            tts_timeout=tts_timeout,
            reference_audio=reference_audio,
            reference_text=reference_text,
            sample_rate=sample_rate,
            fps=fps,
            n_frames=n_frames,
            verbose=verbose,
            run_as_thread=True,
            disable_thread=False,
            tts_api_key="69221550008889493429277623585016",
            gesture_api_key="17248992752111398733945644888484",
        )

        try:
            # Connectivity checks up front (gives fast, clear errors).
            h.assert_ready()

            print("\nMaverickAgentHandler demo is ready.")
            print("Type a sentence and press Enter to speak+gesture.")
            print("Press Enter on an empty line or Ctrl+C to quit.\n")

            while True:
                try:
                    text = input("> ").strip()
                except EOFError:
                    break
                if not text:
                    break
                h.send_agent_text(text)
        except KeyboardInterrupt:
            pass
        finally:
            h.cleanup()

    def assert_ready(self) -> None:
        """Validate that all external components are reachable.

        Raises RuntimeError with actionable guidance on failure.

        If all checks pass, streaming threads are started (if configured).
        """
        self._check_visualizer_connection()
        self._check_gesture_api()
        self._check_tts_api()
        if self.run_as_thread and not self.disable_thread:
            self.start_streaming()

    def _check_visualizer_connection(self) -> None:
        try:
            import websocket  # websocket-client
        except Exception as exc:
            raise RuntimeError(
                "Missing dependency 'websocket-client'. Install it (pip install websocket-client) "
                "to stream to the visualizer."
            ) from exc

        try:
            ws = websocket.create_connection(self.visualizer.url, timeout=3)
            ws.close()
        except Exception as exc:
            raise VisualizerConnectionError(
                f"Could not connect to visualizer websocket at {self.visualizer.url}: {exc}. "
                "Is the visualizer running and listening on that URL?"
            ) from exc

    def _check_gesture_api(self) -> None:
        if not (self.gesture_handler.host and self.gesture_handler.port):
            raise RuntimeError(
                "Gesture API host/port not configured. Provide gesture_host and gesture_port."
            )
        if not self.gesture_handler.api_key:
            raise RuntimeError(
                "Gesture API key not configured. Provide gesture_api_key to MaverickAgentHandler (or set it on the GestureGenerationHandler)."
            )

        # Quick /generate probe with a tiny chunk
        silence = np.zeros((self.chunk_size,), dtype=np.float32)
        try:
            out = self.gesture_handler.generate_results(
                {"audio": silence, "sample_rate": self.sample_rate, "timestamp": time.time()},extra={}
            )
        except Exception as exc:
            raise RuntimeError(
                f"Gesture API request failed: {exc}. If you're seeing 401 Unauthorized, check that "
                f"gesture_api_key matches API_KEY_REALTIMEBEATGESTURE on the server. "
                f"Target: http://{self.gesture_handler.host}:{self.gesture_handler.port}/generate"
            ) from exc

        if not isinstance(out, dict) or ("frame_string" not in out and "bones" not in out):
            raise RuntimeError(f"Gesture API returned unexpected response: {out}")
        if "frame_string" not in out:
            raise RuntimeError(
                "Gesture API did not return 'frame_string'. The Unity visualizer client expects frame strings. "
                "Update the gesture API to include 'frame_string' in its response."
            )

    def _check_tts_api(self) -> None:
        if not (self.tts_handler.host and self.tts_handler.port):
            raise RuntimeError("TTS host/port not configured. Provide tts_host and tts_port.")

        # Minimal round-trip. This is intentionally short to avoid long startup.
        try:
            out = self.tts_handler.generate_results(
                {
                    "text": "Hi.",
                    "reference_audio": self.reference_audio,
                    "reference_text": self.reference_text,
                },extra={}
            )
        except Exception as exc:
            raise RuntimeError(
                f"TTS request failed: {exc}. Is F5-TTS running at http://{self.tts_handler.host}:{self.tts_handler.port}/synthesize ?"
            ) from exc
        if not isinstance(out, dict) or "audio_bytes" not in out:
            raise RuntimeError(f"TTS returned unexpected response: {out}")


class _BytesReader:
    """Minimal file-like wrapper for wave.open without importing io in module namespace."""

    def __init__(self, data: bytes):
        import io

        self._bio = io.BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._bio.read(n)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._bio.seek(offset, whence)

    def tell(self) -> int:
        return self._bio.tell()


def _resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x
    if x.size == 0:
        return x.astype(np.float32)
    ratio = float(sr_out) / float(sr_in)
    n_out = max(1, int(round(x.size * ratio)))
    # positions in input index space
    t = np.linspace(0.0, x.size - 1, num=n_out, dtype=np.float64)
    t0 = np.floor(t).astype(np.int64)
    t1 = np.minimum(t0 + 1, x.size - 1)
    w = (t - t0).astype(np.float32)
    y = (1.0 - w) * x[t0].astype(np.float32) + w * x[t1].astype(np.float32)
    return y.astype(np.float32, copy=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MaverickAgentHandler interactive demo")
    parser.add_argument("--visualizer-url", default="ws://127.0.0.1:1338/Animate")
    parser.add_argument("--gesture-host", default="127.0.0.1")
    parser.add_argument("--gesture-port", type=int, default=42005)
    parser.add_argument("--tts-host", default="127.0.0.1")
    parser.add_argument("--tts-port", type=int, default=8801)
    parser.add_argument("--reference-audio", default="/home/mei/Projects/startmaveric/voices/Enrico Schnick.mp3",
                        help="Path to speaker reference audio (wav/mp3)")
    parser.add_argument("--reference-text", default=None)
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--n-frames", type=int, default=2)
    parser.add_argument("--gesture-timeout", type=float, default=10.0)
    parser.add_argument("--tts-timeout", type=float, default=60.0)
    parser.add_argument("--quiet",default=True, action="store_true")

    args = parser.parse_args()

    MaverickAgentHandler.demo(
        visualizer_url=args.visualizer_url,
        gesture_host=args.gesture_host,
        gesture_port=args.gesture_port,
        tts_host=args.tts_host,
        tts_port=args.tts_port,
        reference_audio=args.reference_audio,
        reference_text=args.reference_text,
        sample_rate=args.sample_rate,
        fps=args.fps,
        n_frames=args.n_frames,
        gesture_timeout=args.gesture_timeout,
        tts_timeout=args.tts_timeout,
        verbose=not args.quiet,
    )

