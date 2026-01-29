import struct
import wave
from typing import Any, Dict

import numpy as np
import pytest

from scs_architecture_handlers.maverick_agent_handler import MaverickAgentHandler, VisualizerConfig


def _make_valid_wav(sr=24000, seconds=0.05) -> bytes:
    n = int(sr * seconds)
    x = (0.1 * np.sin(2 * np.pi * 220 * np.arange(n) / sr)).astype(np.float32)
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype(np.int16)

    import io

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return bio.getvalue()


class _FakeWS:
    def __init__(self):
        self.sent = []

    def send(self, data: str):
        self.sent.append(data)

    def close(self):
        return None


@pytest.fixture
def handler(monkeypatch, tmp_path):
    # Patch websocket.create_connection to avoid real network
    fake_ws = _FakeWS()

    class _FakeWebsocketModule:
        @staticmethod
        def create_connection(url, timeout=5):
            return fake_ws

    monkeypatch.setitem(__import__("sys").modules, "websocket", _FakeWebsocketModule)

    # Make a dummy reference audio file
    ref = tmp_path / "ref.wav"
    ref.write_bytes(_make_valid_wav())

    h = MaverickAgentHandler(
        visualizer=VisualizerConfig(url="ws://127.0.0.1:1338/Animate"),
        gesture_host="localhost",
        gesture_port=5000,
        gesture_api_key="k",
        tts_host="localhost",
        tts_port=8084,
        reference_audio=str(ref),
        run_as_thread=True,
        disable_thread=False,
        verbose=True,
    )

    # Start background streaming (constructor no longer auto-starts to avoid noisy logs on misconfig)
    h.start_streaming()

    # Patch sub-handlers to avoid real HTTP
    def fake_tts_generate(item: Dict[str, Any], **kwargs):
        return {"audio_bytes": _make_valid_wav(sr=24000, seconds=0.08), "content_type": "audio/wav"}

    def fake_gesture_generate(item: Dict[str, Any], **kwargs):
        assert "audio" in item and "sample_rate" in item
        return {"frame_string": "FRAME", "bones": {}}

    monkeypatch.setattr(h.tts_handler, "generate", fake_tts_generate)
    monkeypatch.setattr(h.gesture_handler, "generate", fake_gesture_generate)

    yield h, fake_ws

    h.cleanup()


def test_send_agent_text_queues_and_streams(handler):
    h, fake_ws = handler
    out = h.send_agent_text("Hello")
    assert out["status"] == "queued"

    # Give threads a moment to process
    import time

    time.sleep(0.5)

    # We should have sent at least one websocket message
    assert len(fake_ws.sent) > 0


def test_validation_rejects_bad_item(handler):
    h, _ = handler
    assert h.validate_item({"kind": "agent_text", "text": "ok"}, {})
    assert not h.validate_item({"kind": "agent_text", "text": ""}, {})
    assert not h.validate_item({"kind": "other", "text": "ok"}, {})


def test_assert_ready_calls_components(handler):
    h, _ = handler
    # All dependencies are monkeypatched in the fixture
    h.assert_ready()
