"""F5-TTS handler demo.

This script calls an F5-TTS FastAPI server (default endpoint: /synthesize),
saves the returned audio bytes to a WAV file, and tries to play it back.

It’s intentionally dependency-free: playback uses common Linux CLI tools if
available (pw-play/aplay/paplay/ffplay/mpv). If none are installed, the script
still saves the file and prints its location.

Example:
  python -m src.usage_examples.f5tts_handler_demo \
    --host 127.0.0.1 --port 8084 \
    --reference-audio ./ref.wav \
    --text "Hello from F5-TTS"

Environment variables (optional):
  HOST_F5TTS, PORT_F5TTS, API_KEY_F5TTS
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from scs_architecture_handlers.f5tts_handler import F5TTSHandler


def _pick_player() -> Optional[list[str]]:
    """Return a command argv prefix to play WAV audio, or None if unavailable."""

    # Preference order: PipeWire, ALSA, PulseAudio, ffmpeg, mpv
    candidates: list[list[str]] = [
        ["pw-play"],
        ["aplay"],
        ["paplay"],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error"],
        ["mpv", "--no-video", "--really-quiet"],
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            return cmd
    return None


def _play(path: Path) -> bool:
    player = _pick_player()
    if not player:
        return False

    try:
        subprocess.run([*player, str(path)], check=True)
        return True
    except Exception:
        return False


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Call F5-TTS server and play audio.")
    p.add_argument("--host", default=os.getenv("HOST_F5TTS", "127.0.0.1"))
    p.add_argument("--port", default=os.getenv("PORT_F5TTS", "8801"))
    p.add_argument("--api-key", default=os.getenv("API_KEY_F5TTS", "69221550008889493429277623585016"))
    p.add_argument("--endpoint", default="/synthesize")

    p.add_argument("--text", default="Hello from F5-TTS")
    p.add_argument("--reference-audio", default="/home/mei/Projects/startmaveric/voices/Kathrin Fricke.mp3", help="Path to reference WAV")
    p.add_argument("--reference-text", default=None)
    p.add_argument("--remove-silence", action="store_true")
    p.add_argument("--nfe-steps", type=int, default=32)
    p.add_argument("--speed", type=float, default=1.0)

    p.add_argument("--out", default=None, help="Output WAV path (default: ./outputs/<ts>.wav)")
    p.add_argument("--timeout", type=float, default=30.0)
    args = p.parse_args(argv)

    out_path = Path(args.out) if args.out else Path("outputs") / f"f5tts_{int(time.time())}.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    handler = F5TTSHandler(
        api_key=(args.api_key or None),
        host=args.host,
        port=args.port,
        endpoint_path=args.endpoint,
        run_as_thread=False,
        network_timeout=args.timeout,
    )

    item = {
        "text": args.text,
        "reference_audio": args.reference_audio,
        "reference_text": args.reference_text,
        "remove_silence": bool(args.remove_silence),
        "nfe_steps": int(args.nfe_steps),
        "speed": float(args.speed),
    }

    print("Requesting synthesis...")
    print(f"  url: http://{args.host}:{args.port}{args.endpoint}")
    print(f"  reference_audio: {args.reference_audio}")

    result = handler.generate_results(item,{})
    audio_bytes = result.get("audio_bytes") if isinstance(result, dict) else None
    if not isinstance(audio_bytes, (bytes, bytearray)):
        print("Unexpected result shape:", result)
        return 2

    out_path.write_bytes(bytes(audio_bytes))
    print(f"Saved: {out_path} ({len(audio_bytes)} bytes, content_type={result.get('content_type')})")

    played = _play(out_path)
    if played:
        print("Playback: OK")
    else:
        print("Playback: skipped (no supported player found).")
        print("Try installing one of: pw-play (pipewire), aplay (alsa-utils), paplay (pulseaudio-utils), ffplay (ffmpeg), mpv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
