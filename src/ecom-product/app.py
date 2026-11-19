from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.db import get_db
from .services.embedding import get_embedding_model
from .routes.ai_recommendation_routes import router as ai_recommended_product

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("warming up embedding model and mongodb connection")
    get_embedding_model()
    get_db().command("ping")
    print("System ready to serve requests!")
    yield
    print("Shutting down API gracefully...")


app = FastAPI(
    title="E-Commerce AI Intent & Semantic Recommendation API",
    description="Hybrid Intent Extraction (Groq) + MongoDB Atlas Vector Search Engine",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    ai_recommended_product,
    prefix="/api/v1",
    tags=["Recommendations"]
)