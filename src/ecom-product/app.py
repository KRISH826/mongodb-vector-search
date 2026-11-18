from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.db import get_db
# from .utils.embedding import get_embedding_model
from .routes.ai_recommendation_routes import router as ai_recommended_product

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("warming up embedding model and mongodb connection")
    # get_embedding_model()
    get_db().command("ping")
    print("System ready to serve requests!")
    yield
    print("Shutting down API gracefully...")


