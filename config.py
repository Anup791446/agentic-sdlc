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
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
