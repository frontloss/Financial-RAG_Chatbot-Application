import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = os.getenv("DATA_DIR",str(BASE_DIR/"data"/"financial_reports"))
    DB_PATH = os.getenv("DB_PATH",str(BASE_DIR/"chroma_db"))

    #Models
    LLM_MODEL = "llama3.2"
    EMBED_MODEL = "BAAI/bge-m3"
    LLM_TIMEOUT = 600
    LLM_TEMPERATURE = 0

    #Vector Store
    COLLECTION_NAME = "financial_reports"

settings = Settings()
