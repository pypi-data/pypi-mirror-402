import time
import numpy as np
import pytest
import requests

from gesture_generation_handler import GestureGenerationHandler

# Ensure api_key attribute exists to avoid AttributeError in _prepare_request_payload
GestureGenerationHandler.api_key = ""


def make_audio(length=1000, sr=24000, dtype=np.float32, val_range=(-1.2, 1.2), channels=1):
    rng = np.random.default_rng(123)
    if channels == 1:
        arr = rng.uniform(val_range[0], val_range[1], size=(length,)).astype(dtype)
        return arr
    arr = rng.uniform(val_range[0], val_range[1], size=(length, channels)).astype(dtype)
    return arr


def test_validation_rejects_bad_items():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    assert h.feed("not a dict") is False
    assert h.feed({"audio": make_audio(), "sample_rate": 24000, "timestamp": time.time()}) is True
    # Missing keys
    assert h.feed({"audio": make_audio(), "sample_rate": 24000}) is False
    # Bad sample rate
    assert h.feed({"audio": make_audio(), "sample_rate": -1, "timestamp": time.time()}) is False
    # Bad audio type
    assert h.feed({"audio": [1,2,3], "sample_rate": 24000, "timestamp": time.time()}) is False
    # Wrong ndim
    assert h.feed({"audio": np.ones((10,10,2)), "sample_rate": 24000, "timestamp": time.time()}) is False


def test_preprocess_mono_and_clipping():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    audio = make_audio(channels=2)
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    pre_item, extra = h.preprocess_item(item, {})
    assert pre_item["audio"].ndim == 1
    assert pre_item["audio"].dtype == np.float32
    assert pre_item["audio"].max() <= 1.0 + 1e-6
    assert pre_item["audio"].min() >= -1.0 - 1e-6


def test_prepare_request_payload_structure_and_url_none_when_no_host():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})
    # api_url is None by default, so URL should be None
    assert payload["url"] is None
    assert isinstance(payload["json"], dict)
    assert payload["json"]["sample_rate"] == 24000
    assert isinstance(payload["json"]["audio"], list)


def test_prepare_request_payload_with_host_port():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True, host="localhost", port=5000)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})
    assert payload["url"].endswith("/generate")


def test_dry_run_returns_stub():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    result = h.generate(item)
    assert set(["bones","vad_confidence","fade_strength","inference_ms","ts","sr"]).issubset(result.keys())


def test_postprocess_timestamp_and_sr():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": 999.999}
    stub = {"bones": {}, "vad_confidence": 0.0, "fade_strength": 0.0, "inference_ms": 0.0}
    post = h.postprocess_result(item, {}, stub)
    assert post["ts"] == 999.999
    assert post["sr"] == 24000


def test_network_success(monkeypatch):
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=False, host="localhost", port=5000)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})

    class DummyResp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self):
            return None
        def json(self):
            return self._data

    def fake_post(url, json, timeout):
        assert url.endswith("/generate")
        return DummyResp({"bones": {"joint": [0,1]}, "vad_confidence": 0.5, "fade_strength": 0.1, "inference_ms": 5.2})

    monkeypatch.setattr(requests, "post", fake_post)
    resp = h.perform_request(payload)
    assert "bones" in resp
    assert h.network_error_count == 0


def test_network_error(monkeypatch):
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=False, host="localhost", port=5000)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})

    def fake_post(url, json, timeout):
        raise requests.RequestException("net fail")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(requests.RequestException):
        h.perform_request(payload)
    assert h.network_error_count == 1


def test_threaded_processing():
    h = GestureGenerationHandler(run_as_thread=True, disable_thread=False, dry_run=True)
    try:
        audio = make_audio()
        assert h.feed({"audio": audio, "sample_rate": 24000, "timestamp": time.time()}) is True
        res = h.get_result(timeout=2.0)
        assert res is not None
        assert "bones" in res
    finally:
        h.cleanup()


@pytest.mark.asyncio
async def test_async_generate_and_cleanup():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    audio = make_audio()
    result = await h.async_generate({"audio": audio, "sample_rate": 24000, "timestamp": time.time()})
    assert "bones" in result
    await h.async_cleanup()


def test_stats_last_network_call(monkeypatch):
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=False, host="localhost", port=5000)
    audio = make_audio()
    item = {"audio": audio, "sample_rate": 24000, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})
    class DummyResp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self):
            return None
        def json(self):
            return self._data
    def fake_post(url, json, timeout):
        return DummyResp({"bones": {}, "vad_confidence": 0.0, "fade_strength": 0.0, "inference_ms": 0.0})
    monkeypatch.setattr(requests, "post", fake_post)
    before = h.stats()["last_network_call_at"]
    h.perform_request(payload)
    after = h.stats()["last_network_call_at"]
    assert after is not None and after != before


def test_feed_ignored_when_stopping():
    h = GestureGenerationHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    h.stop_event.set()
    audio = make_audio()
    assert h.feed({"audio": audio, "sample_rate": 24000, "timestamp": time.time()}) is False
