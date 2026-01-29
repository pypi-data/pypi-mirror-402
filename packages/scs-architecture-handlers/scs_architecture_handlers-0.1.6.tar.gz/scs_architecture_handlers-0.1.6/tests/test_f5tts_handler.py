import io
import os
import time
import pytest
import requests

from f5tts_handler import F5TTSHandler


def make_wav_bytes():
    # minimal header + 4 bytes data
    return b"RIFF\x28\x00\x00\x00WAVEfmt " + b"\x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x04\x00\x00\x00\x00\x00\x00\x00"


def test_validation_and_preprocess_with_bytesio(tmp_path):
    h = F5TTSHandler(host="localhost", port=8084)
    ref = io.BytesIO(b"abc")
    item = {"text": "Hallo", "reference_audio": ref, "filename": "ref.wav", "nfe_steps": 16, "speed": 1.2}
    ok = h.validate_item(item, {})
    assert ok
    pre, _ = h.preprocess_item(item, {})
    assert pre["reference_audio_tuple"][0] == "ref.wav"
    assert pre["nfe_steps"] == 16
    assert pre["speed"] == 1.2


def test_dry_run_returns_audio_bytes():
    h = F5TTSHandler(dry_run=True)
    item = {"text": "Hi", "reference_audio": b"data"}
    out = h.generate(item)
    assert isinstance(out, dict)
    assert out["content_type"].startswith("audio/")
    assert isinstance(out["audio_bytes"], (bytes, bytearray))


def test_network_success(monkeypatch):
    h = F5TTSHandler(host="host", port=8084)
    item = {"text": "Test", "reference_audio": b"xyz"}

    class DummyResp:
        def __init__(self):
            self.status_code = 200
            self.content = make_wav_bytes()
            self.headers = {"content-type": "audio/wav"}
        def raise_for_status(self):
            return None

    def fake_post(url, files, data, timeout):
        assert url.endswith("/synthesize")
        assert "reference_audio" in files
        return DummyResp()

    monkeypatch.setattr(requests, "post", fake_post)
    out = h.generate(item)
    assert out["content_type"] == "audio/wav"
    assert out["audio_bytes"].startswith(b"RIFF")


def test_network_error(monkeypatch):
    h = F5TTSHandler(host="host", port=8084)
    item = {"text": "Test", "reference_audio": b"xyz"}

    def fake_post(url, files, data, timeout):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(requests.RequestException):
        h.generate(item)
    assert h.network_error_count == 1


@pytest.mark.asyncio
async def test_async_generate():
    h = F5TTSHandler(dry_run=True)
    out = await h.async_generate({"text": "ok", "reference_audio": b"a"})
    assert "audio_bytes" in out
