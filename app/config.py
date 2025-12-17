import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    # OPENAI_API_KEY setting added for backend key lookup
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()