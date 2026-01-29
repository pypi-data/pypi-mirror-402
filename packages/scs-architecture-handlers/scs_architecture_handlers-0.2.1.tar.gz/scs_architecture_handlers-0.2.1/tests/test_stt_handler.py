import sys
import time
import types
import asyncio
import pytest

from stt_handler import STTHandler


class FakeSTTClient:
    def __init__(self, *args, **kwargs):
        # Default outputs to simulate streaming recognition
        self._outputs = list(kwargs.pop("_outputs", ["hello", "world"]))
    def text(self):
        if self._outputs:
            return self._outputs.pop(0)
        return ""
    def close(self):
        pass


@pytest.fixture(autouse=True)
def patch_realtimestt(monkeypatch):
    mod = types.ModuleType('RealtimeSTT')
    mod.AudioToTextRecorderClient = FakeSTTClient
    monkeypatch.setitem(sys.modules, 'RealtimeSTT', mod)
    yield


def test_stt_handler_produces_results_and_callback():
    received = []
    def cb(item, extra):
        received.append(item)

    h = STTHandler(
        control_url="ws://ctrl",
        data_url="ws://data",
        generate_results_callback=cb,
        run_as_thread=True,
        disable_thread=False,
        poll_interval=0.001,
        use_microphone=False,
    )
    try:
        # Wait up to 1s for at least two callbacks
        deadline = time.time() + 1.0
        while len(received) < 2 and time.time() < deadline:
            time.sleep(0.01)
        assert len(received) >= 2
        # And queue should have some results
        res1 = h.get_result(timeout=0.5)
        assert res1 and res1["type"] == "audio"
        assert "data" in res1
    finally:
        h.cleanup()


def test_feed_is_ignored(caplog):
    h = STTHandler(control_url="a", data_url="b", run_as_thread=False, disable_thread=True)
    assert h.feed("anything") is False


@pytest.mark.asyncio
async def test_async_cleanup_and_start():
    h = STTHandler(control_url="a", data_url="b", run_as_thread=True, disable_thread=False, poll_interval=0.001, use_microphone=False)
    try:
        await h.async_start()
        # Wait up to 1s for one result
        for _ in range(100):
            r = h.get_result(timeout=0.01)
            if r is not None:
                break
            await asyncio.sleep(0.01)
        assert r is not None
    finally:
        await h.async_cleanup()


class CapturingSTTHandler(STTHandler):
    def __init__(self, *args, **kwargs):
        self.hook_calls = []
        super().__init__(*args, **kwargs)
    def _hook_after_generate(self, item, extra, result):
        self.hook_calls.append(("after_generate", result))
        super()._hook_after_generate(item, extra, result)
    def _hook_after_result(self, result):
        self.hook_calls.append(("after_result", result))
        super()._hook_after_result(result)
    def _hook_on_error(self, item, extra, exc):
        self.hook_calls.append(("on_error", str(exc)))
        super()._hook_on_error(item, extra, exc)


def test_hooks_after_generate_and_after_result():
    h = CapturingSTTHandler(
        control_url="ws://ctrl", data_url="ws://data",
        run_as_thread=True, disable_thread=False, use_microphone=False, poll_interval=0.001,
    )
    try:
        # Wait for at least one after_generate
        deadline = time.time() + 1.0
        while not any(c[0] == "after_generate" for c in h.hook_calls) and time.time() < deadline:
            time.sleep(0.01)
        assert any(c[0] == "after_generate" for c in h.hook_calls)
        # Stats should reflect generation
        st = h.stats()
        assert st["processed_count"] >= 1
        assert st["last_result_at"] is not None
        # last_generate_at remains None because STTHandler doesn't call before_generate
        assert st["last_generate_at"] is None
        # After retrieving a result, after_result should be recorded
        _ = h.get_result(timeout=0.5)
        assert any(c[0] == "after_result" for c in h.hook_calls)
    finally:
        h.cleanup()


def test_on_error_hook_invoked_on_exception(monkeypatch):
    # Fake client that raises once, then returns empty
    class ErrOnceClient:
        def __init__(self, *a, **k):
            self._raised = False
        def text(self):
            if not self._raised:
                self._raised = True
                raise RuntimeError("boom")
            return ""
        def close(self):
            pass
    mod = sys.modules['RealtimeSTT']
    monkeypatch.setattr(mod, 'AudioToTextRecorderClient', ErrOnceClient, raising=True)

    h = CapturingSTTHandler(control_url="ws://ctrl", data_url="ws://data", run_as_thread=True, disable_thread=False, use_microphone=False, poll_interval=0.001)
    try:
        # Wait until on_error recorded
        deadline = time.time() + 1.0
        while not any(c[0] == "on_error" for c in h.hook_calls) and time.time() < deadline:
            time.sleep(0.01)
        assert any(c[0] == "on_error" for c in h.hook_calls)
        assert h.error_count >= 1
    finally:
        h.cleanup()


def test_dropped_count_increments_when_result_queue_full(monkeypatch):
    # Client that yields multiple outputs quickly
    class ManyClient:
        def __init__(self, *a, **k):
            self._outs = ["a", "b", "c"]
        def text(self):
            return self._outs.pop(0) if self._outs else ""
        def close(self):
            pass
    mod = sys.modules['RealtimeSTT']
    monkeypatch.setattr(mod, 'AudioToTextRecorderClient', ManyClient, raising=True)

    h = STTHandler(
        control_url="ws://ctrl", data_url="ws://data",
        run_as_thread=True, disable_thread=False, use_microphone=False, poll_interval=0.001,
        result_queue_size=1,
    )
    try:
        # Do not consume immediately to let queue fill
        time.sleep(0.1)
        st = h.stats()
        # One item fits, the rest should drop at put time
        assert st["dropped_count"] >= 1
    finally:
        h.cleanup()


def test_callback_thread_non_blocking_with_slow_callback(monkeypatch):
    # Many outputs quickly
    class ManyClient:
        def __init__(self, *a, **k):
            self._outs = [f"t{i}" for i in range(10)]
        def text(self):
            return self._outs.pop(0) if self._outs else ""
        def close(self):
            pass
    mod = sys.modules['RealtimeSTT']
    monkeypatch.setattr(mod, 'AudioToTextRecorderClient', ManyClient, raising=True)

    # Slow callback simulates heavy work; should not block result production
    called = []
    def slow_cb(item, extra):
        called.append(item)
        time.sleep(0.1)

    h = STTHandler(control_url="c", data_url="d", run_as_thread=True, disable_thread=False,
                   use_microphone=False, poll_interval=0.001, generate_results_callback=slow_cb)
    try:
        # We should be able to get results promptly despite slow callback
        r = h.get_result(timeout=0.2)
        assert r is not None
        # Callback thread should be alive
        assert h.callback_thread is not None and h.callback_thread.is_alive()
    finally:
        h.cleanup()


def test_callback_queue_backpressure_drops(monkeypatch):
    # Many outputs quickly to saturate callback queue
    class ManyClient:
        def __init__(self, *a, **k):
            self._outs = [f"t{i}" for i in range(50)]
        def text(self):
            return self._outs.pop(0) if self._outs else ""
        def close(self):
            pass
    mod = sys.modules['RealtimeSTT']
    monkeypatch.setattr(mod, 'AudioToTextRecorderClient', ManyClient, raising=True)

    def slow_cb(item, extra):
        # Very slow so queue backs up
        time.sleep(0.2)

    h = STTHandler(control_url="c", data_url="d", run_as_thread=True, disable_thread=False,
                   use_microphone=False, poll_interval=0.001, generate_results_callback=slow_cb,
                   result_queue_size=64,  # avoid result queue drops
                   callback_queue_size=1,
                    )
    try:
        # Allow production to run and saturate callback queue
        deadline = time.time() + 1.0
        while h.dropped_count == 0 and time.time() < deadline:
            time.sleep(0.02)
        # We expect some callback drops counted in dropped_count
        assert h.dropped_count >= 1
    finally:
        h.cleanup()


def test_callback_error_increments_error_count(monkeypatch):
    # Fake client to produce one output
    class OneClient:
        def __init__(self, *a, **k):
            self._done = False
        def text(self):
            if not self._done:
                self._done = True
                return "x"
            return ""
        def close(self):
            pass
    mod = sys.modules['RealtimeSTT']
    monkeypatch.setattr(mod, 'AudioToTextRecorderClient', OneClient, raising=True)

    def bad_cb(item, extra):
        raise RuntimeError("cb boom")

    h = STTHandler(control_url="c", data_url="d", run_as_thread=True, disable_thread=False,
                   use_microphone=False, poll_interval=0.001, generate_results_callback=bad_cb)
    try:
        # Wait until error surfaced via callback thread
        deadline = time.time() + 1.0
        while h.error_count == 0 and time.time() < deadline:
            time.sleep(0.01)
        assert h.error_count >= 1
    finally:
        h.cleanup()
