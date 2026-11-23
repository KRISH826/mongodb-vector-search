import os
from dotenv import load_dotenv

load_dotenv()


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is missing from your .env file!")
    return value


class Settings:
    mongodb_uri = require("MONGO_DB_URL")
    db_name = "ecommerce"
    embedding_model = "all-MiniLM-L6-v2"
    embedding_dim = 384
    vector_index_name = "vector_product_index"
    groq_api_model = "openai/gpt-oss-120b"
    groq_api_key = require("GROQ_API_KEY")


settings = Settings()