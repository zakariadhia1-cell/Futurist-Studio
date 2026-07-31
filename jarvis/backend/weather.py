"""Fetches current weather from Open-Meteo (no API key required)."""
import requests

from jarvis.backend.config import JARVIS_LAT, JARVIS_LON

_WEATHER_CODES = {
    0: "klar", 1: "ueberwiegend klar", 2: "teilweise bewoelkt", 3: "bewoelkt",
    45: "neblig", 48: "neblig", 51: "leichter Nieselregen", 53: "Nieselregen",
    55: "starker Nieselregen", 61: "leichter Regen", 63: "Regen", 65: "starker Regen",
    71: "leichter Schneefall", 73: "Schneefall", 75: "starker Schneefall",
    80: "Regenschauer", 81: "Regenschauer", 82: "heftige Regenschauer",
    95: "Gewitter", 96: "Gewitter mit Hagel", 99: "Gewitter mit Hagel",
}


def get_weather_summary() -> str:
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": JARVIS_LAT, "longitude": JARVIS_LON, "current_weather": "true"},
            timeout=5,
        )
        resp.raise_for_status()
        current = resp.json()["current_weather"]
        temp = round(current["temperature"])
        condition = _WEATHER_CODES.get(current["weathercode"], "wechselhaft")
        return f"{temp} Grad und {condition}"
    except Exception:
        return "Wetterdaten aktuell nicht verfuegbar"
