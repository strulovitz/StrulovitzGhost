import os
from dotenv import load_dotenv

load_dotenv()

BASEDIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASEDIR, 'strulovitz.db')}"
)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

OUTPUT_DIR = os.path.join(BASEDIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3")
LLM_SPLIT_ENABLED = os.getenv("LLM_SPLIT_ENABLED", "true").lower() == "true"
