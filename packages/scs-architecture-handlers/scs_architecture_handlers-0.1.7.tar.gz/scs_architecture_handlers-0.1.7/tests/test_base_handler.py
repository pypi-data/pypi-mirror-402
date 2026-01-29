import asyncio
import time
import threading
import queue
import types
import pytest

from base_handler import ArchitectureHandler


class DummyHandler(ArchitectureHandler):
    def __init__(self, *args, **kwargs):
        self.generated = []
        self.hook_calls = []
        super().__init__(*args, **kwargs)

    def validate_item(self, item, extra):
        # Gate by expected_type if provided; else allow anything except None
        if self.expected_type and not isinstance(item, self.expected_type):
            return False
        return item is not None

    def preprocess_item(self, item, extra):
        self.hook_calls.append(("preprocess", item, dict(extra)))
        if isinstance(item, (int, float)):
            return item * 2, {**extra, "preprocessed": True}
        return item, {**extra, "preprocessed": True}

    def generate_results(self, item, extra):
        self.hook_calls.append(("generate", item, dict(extra)))
        # Echo plus marker
        self.generated.append((item, dict(extra)))
        # Simulate optional network hop if flag provided
        if extra.get("network"):
            payload = self._prepare_request_payload(item, extra)
            resp = self.perform_request(payload)
            return {"kind": "network", "resp": resp}
        # Or error if requested
        if extra.get("raise"):
            raise RuntimeError("forced error")
        return {"kind": "local", "value": item, "extra": extra}

    def postprocess_result(self, item, extra, result):
        self.hook_calls.append(("postprocess", item, dict(extra), result))
        # Tag result and return
        if isinstance(result, dict):
            result = {**result, "postprocessed": True}
        return result

    # Expose hooks for counting
    def _hook_before_feed(self, item, extra):
        self.hook_calls.append(("before_feed", item, dict(extra)))

    def _hook_after_feed(self, item, extra, enqueued):
        super()._hook_after_feed(item, extra, enqueued)
        self.hook_calls.append(("after_feed", item, dict(extra), enqueued))

    def _hook_before_generate(self, item, extra):
        super()._hook_before_generate(item, extra)
        self.hook_calls.append(("before_generate", item, dict(extra)))

    def _hook_after_generate(self, item, extra, result):
        super()._hook_after_generate(item, extra, result)
        self.hook_calls.append(("after_generate", item, dict(extra), result))

    def _hook_after_result(self, result):
        self.hook_calls.append(("after_result", result))

    def _hook_network_error(self, payload, exc):
        super()._hook_network_error(payload, exc)
        self.hook_calls.append(("network_error", payload, exc))

    def _hook_on_error(self, item, extra, exc):
        super()._hook_on_error(item, extra, exc)
        self.hook_calls.append(("on_error", item, dict(extra), exc))

    # Deterministic perform_request implementation
    def _perform_request(self, payload):
        if payload.get("extra", {}).get("fail_network"):
            raise ConnectionError("network down")
        return {"ok": True, "echo": payload}


def make_handler(**kwargs):
    # Keep threads disabled by default in tests to avoid flakiness
    return DummyHandler(run_as_thread=False, disable_thread=True, **kwargs)


def test_init_defaults_and_logging(monkeypatch):
    h = make_handler()
    stats = h.stats()
    assert stats["run_as_thread"] is False
    assert isinstance(stats["client_id"], str)
    assert stats["processed_count"] == 0
    assert h.input_queue.qsize() == 0
    assert h.result_queue.qsize() == 0


def test_feed_validation_and_drop_counts():
    h = make_handler(expected_type=int)
    # Valid
    ok = h.feed(1, a=2)
    assert ok is True
    # Invalid type -> dropped
    ok2 = h.feed("bad")
    assert ok2 is False
    assert h.dropped_count >= 1


def test_generate_bypass_queues_and_hooks():
    h = make_handler()
    out = h.generate(3, meta=True)
    assert out["kind"] == "local"
    assert out["postprocessed"] is True
    # preprocess doubled the numeric value
    assert out["value"] == 6
    # hook order contains before_generate, preprocess, generate, postprocess, after_generate
    names = [c[0] for c in h.hook_calls]
    assert "before_generate" in names
    assert "preprocess" in names
    assert "generate" in names
    assert "postprocess" in names
    assert "after_generate" in names


def test_generate_validation_error():
    h = make_handler(expected_type=int)
    with pytest.raises(TypeError):
        h.generate("x")


@pytest.mark.timeout(2)
def test_feed_queue_full_drop(monkeypatch):
    h = make_handler()
    # Monkeypatch input_queue to a tiny queue size 1 and fill it
    h.input_queue = queue.Queue(maxsize=1)
    assert h.feed(1) is True
    # Next one should drop as no worker consumes
    assert h.feed(2) is False
    assert h.dropped_count >= 1


@pytest.mark.timeout(3)
def test_processing_thread_puts_results_and_queue_full_drop():
    # Enable threads to exercise processing loop and result queue overflow
    h = DummyHandler(run_as_thread=True, disable_thread=False, max_queue_size=8, result_queue_size=1)
    try:
        # Feed multiple so result queue overflows (no consumer yet)
        for i in range(3):
            assert h.feed(i)
        # Allow some processing time
        time.sleep(0.2)
        # Only 1 result can be stored
        assert h.result_queue.qsize() == 1
        # When we get one, after_result should be recorded
        r = h.get_result(timeout=0.5)
        assert r is not None
        assert any(c[0] == "after_result" for c in h.hook_calls)
    finally:
        h.cleanup()


@pytest.mark.timeout(2)
@pytest.mark.asyncio
async def test_async_wrappers():
    h = make_handler()
    # async_generate should mirror generate behavior
    out = await h.async_generate(4, flag=True)
    assert out["value"] == 8
    # async_feed/get_result operate on queues
    ok = await h.async_feed(10)
    assert ok is True
    # No consumer, so get_result returns None (timeout)
    res = await h.async_get_result(timeout=0.01)
    assert res is None
    await h.async_cleanup()  # idempotent


@pytest.mark.timeout(2)
def test_context_manager_and_cleanup_idempotent():
    h = make_handler()
    h.cleanup()
    # Second cleanup should be no-op
    h.cleanup()
    # Context manager should start/stop if configured
    with DummyHandler(run_as_thread=True, disable_thread=False) as hh:
        assert hh.processing_thread is not None
        assert hh.processing_thread.is_alive()
    # After context exit, stop_event set
    assert hh.stop_event.is_set()


@pytest.mark.timeout(2)
def test_network_call_success_and_hooks():
    h = make_handler()
    payload = h._prepare_request_payload("x", {"network": True})
    resp = h.perform_request(payload)
    assert resp["ok"] is True
    assert resp["echo"]["client_id"] == h.client_id


@pytest.mark.timeout(2)
def test_network_call_error_path():
    h = make_handler()
    payload = h._prepare_request_payload("x", {"network": True, "fail_network": True})
    with pytest.raises(ConnectionError):
        h.perform_request(payload)
    assert h.network_error_count == 1
    assert any(c[0] == "network_error" for c in h.hook_calls)


@pytest.mark.timeout(2)
def test_error_during_generate_is_caught_in_worker():
    h = DummyHandler(run_as_thread=True, disable_thread=False)
    try:
        assert h.feed(1, **{"raise": True})
        time.sleep(0.1)
        # No result produced due to error
        assert h.result_queue.qsize() == 0
        assert h.error_count == 1
        assert any(c[0] == "on_error" for c in h.hook_calls)
    finally:
        h.cleanup()


@pytest.mark.timeout(2)
def test_stats_structure_and_updates():
    h = make_handler()
    st1 = h.stats()
    assert set([
        "client_id","created_at","last_feed_at","last_generate_at","last_result_at",
        "last_network_call_at","input_queue_size","result_queue_size","run_as_thread",
        "processed_count","dropped_count","error_count","network_error_count"
    ]).issubset(st1.keys())
    h.feed(2)
    st2 = h.stats()
    assert st2["input_queue_size"] >= 1


@pytest.mark.timeout(2)
def test_external_callback_injection():
    def cb(item, extra):
        return {"cb": True, "item": item, "extra": extra}

    h = ArchitectureHandler(run_as_thread=False, disable_thread=True, generate_results_callback=cb)
    out = h.generate("hello", tag=1)
    assert out["cb"] is True
    assert out["item"] == "hello"


@pytest.mark.timeout(2)
def test_warning_when_no_generate_implementation(monkeypatch):
    # Build a plain ArchitectureHandler that doesn't override generate_results
    with pytest.warns(UserWarning):
        dummy = ArchitectureHandler(run_as_thread=False, disable_thread=True)
    # But calling generate should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        dummy.generate("x")


@pytest.mark.timeout(2)
def test_clear_feed():
    h = make_handler()
    # Fill input queue artificially
    for i in range(5):
        h.input_queue.put((i, {}))
    removed = h.clear_feed()
    assert removed == 5
    assert h.input_queue.qsize() == 0


@pytest.mark.timeout(2)
def test_start_when_disabled_and_multiple_calls(caplog):
    h = make_handler()
    # start with disable_thread=True should warn and do nothing
    h.start()
    assert h.processing_thread is None
    # Enable and start
    hh = DummyHandler(run_as_thread=True, disable_thread=False)
    try:
        th = hh.processing_thread
        assert th is not None and th.is_alive()
        # Calling start again should be a no-op
        hh.start()
        assert hh.processing_thread is th
    finally:
        hh.cleanup()


@pytest.mark.timeout(2)
def test_result_timeout_returns_none():
    h = make_handler()
    assert h.get_result(timeout=0.01) is None


@pytest.mark.timeout(2)
@pytest.mark.asyncio
async def test_async_start_and_cleanup_do_not_crash():
    hh = DummyHandler(run_as_thread=True, disable_thread=False)
    try:
        await hh.async_start()
        assert hh.processing_thread is not None
    finally:
        await hh.async_cleanup()


@pytest.mark.timeout(2)
def test_finalize_cleanup_is_idempotent():
    # Ensure calling cleanup twice leaves threads joined
    hh = DummyHandler(run_as_thread=True, disable_thread=False)
    try:
        time.sleep(0.05)
    finally:
        hh.cleanup()
        hh.cleanup()
        assert hh._cleaned is True


@pytest.mark.timeout(2)
def test_feed_ignored_when_stopping():
    h = make_handler()
    h.stop_event.set()
    assert h.feed(123) is False


class CallbackEmitterHandler(ArchitectureHandler):
    """Minimal handler that emits async callbacks from generate_results without using queues."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def validate_item(self, item, extra):
        return True
    def generate_results(self, item, extra):
        # Schedule the external callback asynchronously and return quickly
        self._emit_async_callback({"item": item}, dict(extra))
        return {"ok": True, "item": item}


@pytest.mark.timeout(2)
def test_base_callback_thread_non_blocking_with_slow_callback():
    called = []
    def slow_cb(item, extra):
        called.append(item)
        time.sleep(0.1)

    # Disable processing thread; enable callback thread usage
    h = CallbackEmitterHandler(
        run_as_thread=False,
        disable_thread=False,
        generate_results_callback=slow_cb,
    )
    try:
        t0 = time.time()
        out = h.generate("x")
        t1 = time.time()
        # generate should return quickly (well under the slow callback sleep)
        assert out["ok"] is True
        assert (t1 - t0) < 0.05
        # Callback thread should be alive
        assert h.callback_thread is not None and h.callback_thread.is_alive()
        # Eventually the callback should run
        deadline = time.time() + 1.0
        while len(called) < 1 and time.time() < deadline:
            time.sleep(0.01)
        assert len(called) >= 1
    finally:
        h.cleanup()


@pytest.mark.timeout(2)
def test_base_callback_queue_backpressure_drops():
    def slow_cb(item, extra):
        time.sleep(0.2)

    h = CallbackEmitterHandler(
        run_as_thread=False,
        disable_thread=False,
        generate_results_callback=slow_cb,
        callback_queue_size=1,
    )
    try:
        # Rapidly schedule more callbacks than the queue can hold
        for _ in range(10):
            h.generate("y")
        # Allow time for queue to fill and drops to be registered
        time.sleep(0.2)
        assert h.dropped_count >= 1
    finally:
        h.cleanup()


@pytest.mark.timeout(2)
def test_base_callback_error_increments_error_count():
    def bad_cb(item, extra):
        raise RuntimeError("callback boom")

    h = CallbackEmitterHandler(
        run_as_thread=False,
        disable_thread=False,
        generate_results_callback=bad_cb,
    )
    try:
        h.generate("z")
        # Wait for callback thread to handle the exception
        deadline = time.time() + 1.0
        while h.error_count == 0 and time.time() < deadline:
            time.sleep(0.01)
        assert h.error_count >= 1
    finally:
        h.cleanup()

