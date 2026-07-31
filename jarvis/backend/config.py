"""Central configuration for the Jarvis backend, loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Person ---
MASTER_NAME = os.getenv("JARVIS_MASTER_NAME", "Z")

# --- Claude (the "brain") ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_VISION_MODEL = os.getenv("ANTHROPIC_VISION_MODEL", ANTHROPIC_MODEL)

# --- ElevenLabs (voice) ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# --- Weather (Open-Meteo, no key required) ---
JARVIS_LAT = float(os.getenv("JARVIS_LAT", "52.52"))
JARVIS_LON = float(os.getenv("JARVIS_LON", "13.405"))

# --- News feed (public RSS, no key required) ---
NEWS_RSS_URL = os.getenv("NEWS_RSS_URL", "https://www.tagesschau.de/xml/rss2")

# --- Browser control ---
BROWSER_HEADLESS = os.getenv("JARVIS_BROWSER_HEADLESS", "false").lower() == "true"

# --- Tasks shown during "Jarvis activate" ---
TASKS_FILE = os.getenv("JARVIS_TASKS_FILE", os.path.join(os.path.dirname(__file__), "tasks.json"))

# --- Server ---
CORS_ORIGINS = os.getenv("JARVIS_CORS_ORIGINS", "*").split(",")
