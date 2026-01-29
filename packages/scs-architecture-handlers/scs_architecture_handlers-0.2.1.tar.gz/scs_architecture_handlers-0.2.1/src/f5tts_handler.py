from __future__ import annotations

import io
import os
import time
from typing import Any, Dict, Optional, Union

import requests

from base_handler import ArchitectureHandler


class F5TTSHandler(ArchitectureHandler):
    """Client handler for an F5-TTS FastAPI server.

    On demand, generate speech given text and a reference audio using the server's
    `/synthesize` endpoint.

    Inputs:
      item: dict with keys
        - text: str
        - reference_audio: Union[str, bytes, io.BytesIO]
        - reference_text: Optional[str]
        - remove_silence: Optional[bool] (default False)
        - nfe_steps: Optional[int] (default 32)
        - speed: Optional[float] (default 1.0)
        - filename: Optional[str] (hint for upload filename if using bytes)

    Output (postprocessed):
      dict with keys { 'audio_bytes': bytes, 'content_type': 'audio/wav', 'ts': float }

    Configuration:
      - host and port define the base URL
      - endpoint_path: default '/synthesize'
      - dry_run: if True, returns a short silent wav-like bytes without HTTP.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[Union[int, str]] = None,
        endpoint_path: str = "/synthesize",
        dry_run: bool = False,
        # base args
        run_as_thread: bool = False,
        disable_thread: bool = True,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        expected_type: Optional[type] = None,
        network_timeout: Optional[float] = 30.0,
        client_id_prefix: str = "client",
        generate_results_callback: Optional[Any] = None,
    ) -> None:
        super().__init__(
            host=host,
            port=int(port) if port is not None else None,
            auth=None,
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
        self.endpoint_path = endpoint_path
        self.dry_run = bool(dry_run)
        self.api_key = api_key

    # ---- Validation & preprocessing ----
    def validate_item(self, item: Any, extra: Dict[str, Any]) -> bool:  # type: ignore[override]
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("text"), str):
            return False
        if "reference_audio" not in item:
            return False
        # Allow str path, bytes, or BytesIO
        ra = item["reference_audio"]
        if not isinstance(ra, (str, bytes, io.BytesIO)):
            return False
        # Optional fields type checks
        if "remove_silence" in item and not isinstance(item["remove_silence"], bool):
            return False
        if "nfe_steps" in item and not isinstance(item["nfe_steps"], int):
            return False
        if "speed" in item and not isinstance(item["speed"], (int, float)):
            return False
        if "reference_text" in item and item["reference_text"] is not None and not isinstance(item["reference_text"], str):
            return False
        return True

    def preprocess_item(self, item: Dict[str, Any], extra: Dict[str, Any]):  # type: ignore[override]
        """Normalize the reference audio into a `(filename, fileobj)` tuple.

        For on-disk paths we open the file; callers should rely on `_perform_request`
        to close the handle after the request.
        """

        ref = item["reference_audio"]

        if isinstance(ref, str):
            filename = item.get("filename") or os.path.basename(ref)
            fileobj = open(ref, "rb")
        elif isinstance(ref, (bytes, bytearray)):
            filename = item.get("filename") or "reference.wav"
            fileobj = io.BytesIO(bytes(ref))
        elif isinstance(ref, io.BytesIO):
            filename = item.get("filename") or "reference.wav"
            fileobj = ref
            try:
                fileobj.seek(0)
            except Exception:
                pass
        else:
            # validate_item should prevent this, but keep a safe fallback.
            filename = item.get("filename") or "reference.wav"
            fileobj = io.BytesIO(b"")

        norm = {
            "text": item.get("text", "").strip(),
            "reference_audio_tuple": (filename, fileobj),
            "remove_silence": bool(item.get("remove_silence", False)),
            "nfe_steps": int(item.get("nfe_steps", 32)),
            "speed": float(item.get("speed", 1.0)),
            "reference_text": item.get("reference_text", None),
        }
        return norm, extra

    # ---- Generation ----
    def generate_results(self, item: Dict[str, Any], extra: Dict[str, Any]):  # type: ignore[override]
        payload = self._prepare_request_payload(item, extra)
        return self.perform_request(payload)

    def postprocess_result(self, item: Dict[str, Any], extra: Dict[str, Any], result: Any):  # type: ignore[override]
        # Attach timestamp and content type, pass through bytes
        if isinstance(result, dict) and "audio_bytes" in result:
            result = {**result, "ts": time.time()}
        return result

    # ---- Networking ----
    def _endpoint_url(self) -> Optional[str]:
        if not (self.host and self.port):
            return None
        return f"http://{self.host}:{self.port}{self.endpoint_path}"

    def _prepare_request_payload(self, item: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        # If dry_run or no URL, short-circuit
        url = self._endpoint_url()
        api_key = (self.api_key or "").strip()
        headers: Dict[str, str] = {}
        if api_key:
            # Server code uses `x_api_key` (FastAPI header param name). Keep `x-api-key` for compatibility.
            headers["x_api_key"] = api_key
            headers["x-api-key"] = api_key
        return {
            "url": url,
            "item": item,
            "timeout": float(self.network_timeout or 30.0),
            "headers": headers,
        }

    def _perform_request(self, payload: Dict[str, Any]) -> Any:  # type: ignore[override]
        if self.dry_run or not payload.get("url"):
            # Return a tiny fake WAV header + data (not a valid full wav, but good enough for tests)
            fake = (
                b"RIFF\x28\x00\x00\x00WAVEfmt "
                + b"\x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x04\x00\x00\x00\x00\x00\x00\x00"
            )
            return {"audio_bytes": fake, "content_type": "audio/wav"}

        url: str = payload["url"]
        item: Dict[str, Any] = payload["item"]
        timeout: float = payload.get("timeout", 30.0)
        headers: Dict[str, str] = payload.get("headers", {})

        # Build multipart form
        pre_item, _ = self.preprocess_item(item, {})
        filename, fileobj = pre_item["reference_audio_tuple"]

        # requests expects (filename, fileobj, content_type?) tuples for multipart
        files = {"reference_audio": (filename, fileobj)}

        # FastAPI `Form(...)` values arrive as strings; send strings explicitly.
        data = {
            "text": str(pre_item["text"]),
            "remove_silence": "true" if pre_item["remove_silence"] else "false",
            "nfe_steps": str(int(pre_item["nfe_steps"])),
            "speed": str(float(pre_item["speed"])),
            "reference_text": str(pre_item["reference_text"] or ""),
        }

        try:
            resp = requests.post(url, files=files, data=data, headers=headers, timeout=timeout)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "application/octet-stream")
            return {"audio_bytes": resp.content, "content_type": content_type}
        finally:
            # Close only if we opened a real file handle.
            try:
                if hasattr(fileobj, "close") and isinstance(item.get("reference_audio"), str):
                    fileobj.close()
            except Exception:
                pass


#files = {"reference_audio": open(reference_audio_path, "rb")}
    # data = {
    #     "text": text,
    #     "remove_silence": str(remove_silence).lower(),
    #     "nfe_steps":12,
    #     "speed":0.9,
    #     "reference_text":reference_text
    # }
    #
    # try:
    #     print("Uploading reference audio and requesting synthesis...")
    #     response = requests.post(API_URL, files=files, data=data)
