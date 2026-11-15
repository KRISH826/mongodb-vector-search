import os
from dotenv import load_dotenv

load_dotenv()

def _require(env: str) -> str:
    value = os.getenv(env)
    if not value:
        raise ValueError(f"{env} is missing from your .env file!")
    return value

class Settings:
    mongodb_uri = _require("MONGO_DB_URL")
    deepseek_api_key = _require("DEEPSEEK_API_KEY")
    embedding_model = "all-MiniLM-L6-v2"
    embedding_dim = 384


settings = Settings()
