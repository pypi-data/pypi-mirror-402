import io
import pytest
import requests

from scs_architecture_handlers.f5tts_handler import F5TTSHandler


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
    h = F5TTSHandler(host="host", port=8084, api_key="secret")
    item = {"text": "Test", "reference_audio": b"xyz", "remove_silence": True, "nfe_steps": 12, "speed": 0.9}

    class DummyResp:
        def __init__(self):
            self.status_code = 200
            self.content = make_wav_bytes()
            self.headers = {"content-type": "audio/wav"}

        def raise_for_status(self):
            return None

    def fake_post(url, files, data, headers, timeout):
        assert url.endswith("/synthesize")
        assert "reference_audio" in files
        # Required form keys
        assert set(["text", "remove_silence", "nfe_steps", "speed"]).issubset(set(data.keys()))
        # FastAPI Form values come in as strings; ensure we send strings.
        assert isinstance(data["text"], str)
        assert data["remove_silence"] in {"true", "false"}
        assert data["nfe_steps"].isdigit()
        float(data["speed"])  # parseable
        # Required auth header for the server implementation (new versions)
        assert headers.get("x_api_key") == "secret"
        return DummyResp()

    monkeypatch.setattr(requests, "post", fake_post)
    out = h.generate(item)
    assert out["content_type"] == "audio/wav"
    assert out["audio_bytes"].startswith(b"RIFF")


def test_network_error(monkeypatch):
    h = F5TTSHandler(host="host", port=8084)
    item = {"text": "Test", "reference_audio": b"xyz"}

    def fake_post(url, files, data, headers, timeout):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(requests.RequestException):
        h.generate(item)
    assert h.network_error_count == 1


# NOTE: We intentionally don't test async wrappers here because this repo doesn't
# depend on pytest-asyncio/anyio test runners. The async wrappers live in
# ArchitectureHandler and are exercised in integration contexts.
