"""Runs locally on Z's machine: listens to the microphone for a double-clap and
launches apps + activates Jarvis (calls the backend's /api/activate).

This does NOT run inside the backend/container - it needs local mic + speaker
hardware, so start it on your own computer:

    pip install -r jarvis/clap_trigger/requirements.txt
    python jarvis/clap_trigger/clap_listener.py
"""
import base64
import os
import platform
import subprocess
import sys
import tempfile
import time

import numpy as np
import requests
import sounddevice as sd

JARVIS_URL = os.getenv("JARVIS_URL", "http://localhost:8000")
SAMPLE_RATE = 16000
BLOCK_SIZE = 512

CLAP_THRESHOLD = float(os.getenv("JARVIS_CLAP_THRESHOLD", "0.35"))  # peak amplitude, 0-1
CLAP_REFRACTORY_S = 0.12       # ignore new peaks for this long after one is detected
DOUBLE_CLAP_MIN_GAP_S = 0.12   # minimum time between the two claps
DOUBLE_CLAP_MAX_GAP_S = 0.9    # maximum time between the two claps

# app-name -> (platform -> shell command)
APP_COMMANDS = {
    "spotify": {
        "Darwin": ["open", "-a", "Spotify"],
        "Windows": ["cmd", "/c", "start", "spotify:"],
        "Linux": ["spotify"],
    },
    "vscode": {
        "Darwin": ["open", "-a", "Visual Studio Code"],
        "Windows": ["cmd", "/c", "code"],
        "Linux": ["code"],
    },
    "obsidian": {
        "Darwin": ["open", "-a", "Obsidian"],
        "Windows": ["cmd", "/c", "start", "obsidian://open"],
        "Linux": ["obsidian"],
    },
}

APPS_TO_LAUNCH = [a.strip() for a in os.getenv("JARVIS_CLAP_APPS", "spotify,vscode,obsidian").split(",") if a.strip()]


def launch_apps() -> None:
    system = platform.system()
    for app in APPS_TO_LAUNCH:
        command = APP_COMMANDS.get(app, {}).get(system)
        if not command:
            print(f"[clap] Kein Start-Befehl fuer '{app}' auf {system} hinterlegt, ueberspringe.")
            continue
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[clap] Gestartet: {app}")
        except Exception as exc:
            print(f"[clap] Konnte '{app}' nicht starten: {exc}")


def play_audio_file(path: str) -> None:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", path], check=False)
        elif system == "Windows":
            os.startfile(path)  # noqa: S606 - intentional local playback
        else:
            for player in ("mpg123", "ffplay", "cvlc", "xdg-open"):
                try:
                    args = [player, path] if player != "ffplay" else [player, "-nodisp", "-autoexit", path]
                    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
    except Exception as exc:
        print(f"[clap] Audiowiedergabe fehlgeschlagen: {exc}")


def activate_jarvis() -> None:
    print("[clap] Doppelklatschen erkannt -> aktiviere Jarvis")
    launch_apps()
    try:
        resp = requests.post(f"{JARVIS_URL}/api/activate", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"[clap] Jarvis: {data['text']}")
        if data.get("audio_base64"):
            audio_bytes = base64.b64decode(data["audio_base64"])
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            play_audio_file(tmp_path)
            os.unlink(tmp_path)
    except Exception as exc:
        print(f"[clap] Konnte Jarvis nicht aktivieren: {exc}")


def main() -> None:
    print(f"[clap] Lausche auf Doppelklatschen (Backend: {JARVIS_URL}) ... Strg+C zum Beenden.")
    last_clap_time = None
    refractory_until = 0.0

    def callback(indata, frames, time_info, status):
        nonlocal last_clap_time, refractory_until
        now = time.monotonic()
        peak = float(np.max(np.abs(indata)))
        if peak < CLAP_THRESHOLD or now < refractory_until:
            return
        refractory_until = now + CLAP_REFRACTORY_S

        if last_clap_time is None:
            last_clap_time = now
            return

        gap = now - last_clap_time
        if DOUBLE_CLAP_MIN_GAP_S <= gap <= DOUBLE_CLAP_MAX_GAP_S:
            last_clap_time = None
            activate_jarvis()
        else:
            last_clap_time = now

    with sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        callback=callback,
    ):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[clap] Beendet.")
            sys.exit(0)


if __name__ == "__main__":
    main()
