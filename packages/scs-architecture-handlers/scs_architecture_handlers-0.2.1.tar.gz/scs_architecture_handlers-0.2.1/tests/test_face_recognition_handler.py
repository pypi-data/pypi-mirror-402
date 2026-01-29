import io
import time
import threading
import numpy as np
import pytest
import requests

from face_recognition_handler import FaceRecognitionHandler


def make_frame(h=32, w=32, c=3, dtype=np.uint8, value_range=(0,255)):
    if dtype == np.uint8:
        return np.random.randint(value_range[0], value_range[1]+1, (h,w,c), dtype=dtype)
    arr = np.random.uniform(value_range[0], value_range[1], (h,w,c)).astype(dtype)
    return arr


def test_validation_rejects_wrong_types():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    assert h.feed("not a dict") is False
    assert h.feed({"frame": make_frame(), "timestamp": time.time()}) is True  # missing other keys ok? REQUIRED_KEYS frame,timestamp only
    # Wrong frame type
    bad_item = {"frame": np.random.rand(10), "timestamp": time.time()}
    assert h.feed(bad_item) is False
    # Wrong ndim
    bad_nd = {"frame": np.random.randint(0,255,(10,10), dtype=np.uint8), "timestamp": time.time()}
    assert h.feed(bad_nd) is False


def test_preprocess_converts_to_uint8_and_clips():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    frame = make_frame(dtype=np.float32, value_range=(0,300))  # values exceed 255
    item = {"frame": frame, "timestamp": time.time()}
    pre_item, extra = h.preprocess_item(item, {})
    assert pre_item["frame"].dtype == np.uint8
    assert pre_item["frame"].max() <= 255


def test_prepare_request_payload_contains_jpeg_bytes_and_headers():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True, api_key="KEY", process_stream="stream1", host="localhost", port=8000)
    frame = make_frame()
    item = {"frame": frame, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})
    assert payload["client_id"] == h.client_id
    assert payload["headers"]["x-api-key"] == "KEY"
    assert payload["headers"]["process-stream"] == "stream1"
    assert payload["url"].endswith("/detect")
    # JPEG magic numbers FF D8 at start FF D9 at end
    data = payload["image_bytes"]
    assert data[:2] == b"\xff\xd8"
    assert data[-2:] == b"\xff\xd9"


def test_dry_run_perform_request_returns_stub():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    frame = make_frame()
    item = {"frame": frame, "timestamp": time.time()}
    result = h.generate(item)
    assert isinstance(result, dict)
    assert set(["detectedPersons","numPersons","fps","ts"]).issubset(result.keys())


def test_postprocess_attaches_timestamp():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    frame = make_frame()
    item = {"frame": frame, "timestamp": 123.456}
    payload = h._prepare_request_payload(item, {})
    stub_resp = {"detectedPersons": [], "numPersons": 0, "fps": 0.0}
    post = h.postprocess_result(item, {}, stub_resp)
    assert post["ts"] == 123.456


def test_network_path_success(monkeypatch):
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=False, api_key="A", host="localhost", port=9999)
    frame = make_frame()
    item = {"frame": frame, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})

    class DummyResp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self):
            return None
        def json(self):
            return self._data

    def fake_post(url, headers, files, timeout):
        assert url.endswith("/detect")
        assert "file" in files
        return DummyResp({"detectedPersons": ["x"], "numPersons": 1, "fps": 12.3})

    monkeypatch.setattr(requests, "post", fake_post)
    resp = h.perform_request(payload)
    assert resp["numPersons"] == 1
    assert h.network_error_count == 0


def test_network_path_error(monkeypatch):
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=False, api_key="A", host="localhost", port=9999)
    frame = make_frame()
    item = {"frame": frame, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})

    def fake_post(url, headers, files, timeout):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(requests.RequestException):
        h.perform_request(payload)
    assert h.network_error_count == 1


def test_thread_processing_and_result_queue():
    h = FaceRecognitionHandler(run_as_thread=True, disable_thread=False, dry_run=True)
    try:
        frame = make_frame()
        assert h.feed({"frame": frame, "timestamp": time.time()}) is True
        res = h.get_result(timeout=2.0)
        assert res is not None
        assert "numPersons" in res
    finally:
        h.cleanup()


@pytest.mark.asyncio
async def test_async_generate_and_cleanup():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    frame = make_frame()
    result = await h.async_generate({"frame": frame, "timestamp": time.time()})
    assert "numPersons" in result
    await h.async_cleanup()


def test_stats_network_timestamp_updates(monkeypatch):
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=False, api_key="A", host="localhost", port=1111)
    frame = make_frame()
    item = {"frame": frame, "timestamp": time.time()}
    payload = h._prepare_request_payload(item, {})

    class DummyResp:
        def __init__(self):
            self._data = {"detectedPersons": [], "numPersons": 0, "fps": 0.0}
        def raise_for_status(self):
            return None
        def json(self):
            return self._data

    def fake_post(url, headers, files, timeout):
        return DummyResp()

    monkeypatch.setattr(requests, "post", fake_post)
    before = h.stats()["last_network_call_at"]
    h.perform_request(payload)
    after = h.stats()["last_network_call_at"]
    assert after is not None
    assert before != after


def test_feed_during_stop_event_is_ignored():
    h = FaceRecognitionHandler(run_as_thread=False, disable_thread=True, dry_run=True)
    h.stop_event.set()
    frame = make_frame()
    assert h.feed({"frame": frame, "timestamp": time.time()}) is False


def test_webcam_mode_uses_latest_frame_only_and_async_callback_thread():
    # Provide three frames quickly. Processing is slowed down a bit to create backpressure.
    frames = [make_frame() for _ in range(3)]
    idx = {"i": 0}

    def provider():
        if idx["i"] >= len(frames):
            return None
        f = frames[idx["i"]]
        idx["i"] += 1
        return f

    callback_threads = []
    callback_results = []
    callback_event = threading.Event()

    def on_result(result, extra):
        callback_threads.append(threading.current_thread().name)
        callback_results.append(result)
        callback_event.set()
        # simulate some work
        time.sleep(0.05)

    h = FaceRecognitionHandler(
        run_as_thread=True,
        disable_thread=False,
        dry_run=True,
        auto_webcam=True,
        webcam_fps=None,
        webcam_frame_provider=provider,
        generate_results_callback=on_result,
    )

    # Monkeypatch generate_results to be slower so webcam producer outpaces processing.
    orig_generate_results = h.generate_results

    def slow_generate(item, extra):
        time.sleep(0.05)
        return orig_generate_results(item, extra)

    h.generate_results = slow_generate  # type: ignore[assignment]

    try:
        # Wait for at least one callback invocation
        assert callback_event.wait(timeout=2.0)

        # The callback must be invoked on ResultCallback-* thread, not on processing thread.
        assert any(name.startswith("ResultCallback-") for name in callback_threads)

        # Ensure that processing produced a result and it includes ts
        res = h.get_result(timeout=2.0)
        assert res is not None and "ts" in res

        # With a maxsize=1 input queue, we should have dropped at least one frame under backpressure.
        assert h.input_queue.maxsize == 1
        assert h.webcam_drop_count >= 0
    finally:
        h.cleanup()
