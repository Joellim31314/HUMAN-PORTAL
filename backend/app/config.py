import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SIM_CACHE_DIR = DATA_DIR / "simulations"

AGENTS_PATH = PROCESSED_DIR / "agents.json"
STORES_PATH = PROCESSED_DIR / "stores.json"

# Population
POPULATION_SIZE = int(os.getenv("POPULATION_SIZE", "2000"))
POPULATION_SEED = int(os.getenv("POPULATION_SEED", "7"))

# LLM (DeepSeek, OpenAI-compatible). No key -> template fallbacks.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "16"))
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "45"))
INTERVIEW_COUNT = int(os.getenv("INTERVIEW_COUNT", "80"))

# Engine
WALK_RADIUS_M = float(os.getenv("WALK_RADIUS_M", "400"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
