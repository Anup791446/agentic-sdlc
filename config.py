# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = "gpt-4o"  # or "gpt-4-turbo", "gpt-3.5-turbo"
    MAX_RETRIES: int = 3
    OUTPUT_DIR: str = "outputs"
    
    @classmethod
    def is_mock_mode(cls) -> bool:
        return os.getenv("MOCK_MODE", "false").lower() in ("1", "true", "yes")

    @classmethod
    def validate(cls):
        if not cls.is_mock_mode() and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
