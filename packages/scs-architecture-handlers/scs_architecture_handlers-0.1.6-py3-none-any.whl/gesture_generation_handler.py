"""Gesture Generation Handler that calls an external FastAPI gesture API.

It sends audio chunks to /generate as JSON and returns the processed data.
Run directly to try a dry-run demo (no network required) or set env vars to
call a live server.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Callable, Optional

import numpy as np
import requests

from base_handler import ArchitectureHandler


class GestureGenerationHandler(ArchitectureHandler):
    """Posts audio chunks to a remote /generate endpoint.

    Expected item shape:
    {
        "audio": np.ndarray,   # mono float32/float64 in [-1, 1], shape (N,) or (N, 1) or (N, C)
        "sample_rate": int,    # e.g., 24000
        "timestamp": float,    # seconds
    }

    Parameters (in addition to base ArchitectureHandler):
    - dry_run: bool                If True, skip network call and return a stub result
    """

    REQUIRED_KEYS = {"audio", "sample_rate", "timestamp"}

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        dry_run: bool = False,
        # Base parameters
        host: Optional[str] = None,
        port: Optional[int] = None,
        auth: Any = None,
        run_as_thread: bool = True,
        disable_thread: bool = False,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        expected_type: Optional[type] = None,
        network_timeout: Optional[float] = 10.0,
        client_id_prefix: str = "client",
        generate_results_callback: Optional[
            Callable[[Any, Dict[str, Any]], Any]
        ] = None,  # type: ignore[name-defined]
    ):
        super().__init__(
            host=host,
            port=port,
            auth=auth,
            run_as_thread=run_as_thread,
            disable_thread=disable_thread,
            max_queue_size=max_queue_size,
            result_queue_size=result_queue_size,
            verbose=verbose,
            expected_type=expected_type,
            network_timeout=network_timeout,
            client_id_prefix=client_id_prefix,
            generate_results_callback=generate_results_callback,
        )
        self.api_key: Optional[str] = api_key
        self.dry_run: bool = bool(dry_run)
        self._timeout: float = float(self.network_timeout or 10.0)

    # --- Validation / Preprocess ---
    def validate_item(self, item: Dict[str, Any], extra: Dict[str, Any]) -> bool:  # type: ignore[override]
        if not isinstance(item, dict):
            return False
        if not self.REQUIRED_KEYS.issubset(item.keys()):
            return False
        audio = item.get("audio")
        sr = item.get("sample_rate")
        if not isinstance(audio, np.ndarray):
            return False
        if audio.ndim not in (1, 2):
            return False
        if not isinstance(sr, (int, np.integer)) or sr <= 0:
            return False
        return True

    def preprocess_item(self, item: Dict[str, Any], extra: Dict[str, Any]):  # type: ignore[override]
        audio: np.ndarray = item["audio"]
        # Convert to mono if multi-channel
        if audio.ndim == 2:
            if audio.shape[1] > 1:
                audio = np.mean(audio, axis=1)
            else:
                audio = audio[:, 0]
        # Ensure float32 and bounded [-1, 1]
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32, copy=False)
        if np.any(audio < -1.0) or np.any(audio > 1.0):
            audio = np.clip(audio, -1.0, 1.0)
        return {**item, "audio": audio}, extra

    # --- Core generation ---
    def generate_results(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Any:  # type: ignore[override]
        payload = self._prepare_request_payload(item, extra)
        return self.perform_request(payload)

    def postprocess_result(self, item: Dict[str, Any], extra: Dict[str, Any], result: Any) -> Any:  # type: ignore[override]
        if isinstance(result, dict):
            result = {**result, "ts": item["timestamp"], "sr": item["sample_rate"]}
        return result

    # --- Networking helpers ---
    def _prepare_request_payload(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        audio: np.ndarray = item["audio"]
        sr: int = int(item["sample_rate"])
        body = {
            "audio": audio.tolist(),
            "sample_rate": sr,
        }
        return {
            "url": self._generate_url(),
            "json": body,
            "timeout": self._timeout,
            "headers": {
                "x-api-key": self.api_key or "",
            },
        }

    def _perform_request(self, payload: Dict[str, Any]):  # type: ignore[override]
        if self.dry_run or not payload.get("url"):
            # Stubbed plausible structure
            return {
                "bones": {},
                "vad_confidence": 0.0,
                "fade_strength": 0.0,
                "inference_ms": 0.0,
            }
        url = payload["url"]
        timeout = payload.get("timeout", self._timeout)
        resp = requests.post(url, json=payload["json"], timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # --- URL helpers ---
    def _generate_url(self) -> Optional[str]:
        if not (self.host and self.port):
            return None
        return f"http://{self.host}:{self.port}/generate"


def _demo():
    # Demo: generate a short sine tone chunk and process it
    dry_run = True

    handler = GestureGenerationHandler(
        host=os.getenv("GESTURE_API_HOST") or "localhost",
        port=os.getenv("GESTURE_PORT") or 5000,
        dry_run=dry_run,
        run_as_thread=True,
        verbose=True,
        network_timeout=10.0,
    )

    # Create a 0.5s sine at 240 Hz, sr=24000
    sr = 24000
    t = np.arange(0, int(0.5 * sr)) / sr
    audio = 0.2 * np.sin(2 * np.pi * 240 * t).astype(np.float32)

    handler.feed({"audio": audio, "sample_rate": sr, "timestamp": time.time()})
    result = handler.get_result(timeout=5.0)
    print("Gesture result:", result)
    print("Stats:", handler.stats())
    handler.cleanup()


if __name__ == "__main__":
    _demo()
