import os
from dotenv import load_dotenv

load_dotenv()


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DB_PATH = os.getenv("DB_PATH", "stock_assistant/data/stocks.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "stock_assistant/chroma_store")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "macro_docs")


class AppConfig:
    APP_NAME = "stock_assistant"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Stock Investment Research Assistant"
    APP_AUTHOR = "Mohammad Ariful Islam"
    APP_AUTHOR_EMAIL = "[EMAIL_ADDRESS]"
    APP_LICENSE = "MIT"
    APP_KEYWORDS = ["stock", "investment", "research", "assistant"]
    APP_URL = "http://localhost:8000"
    APP_DEBUG = True
    APP_ENV = "development"
    APP_DEBUG = True

