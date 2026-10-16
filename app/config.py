### FILE: app/config.py
"""Application configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ATTRACTIONS_FILE = DATA_DIR / "attractions.csv"
MEMORY_DB_FILE = DATA_DIR / "travel_memory.db"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Operational defaults
DEFAULT_DAILY_FOOD_PER_PERSON = 500.0
DEFAULT_DAILY_TRANSPORT_TOTAL = 500.0
DEFAULT_ROOM_PER_NIGHT = 1500.0