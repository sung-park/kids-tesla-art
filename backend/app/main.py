from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import process


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Kids Tesla Art API",
    version="0.1.0",
    description="Image processing API for transforming children's drawings into Tesla wraps",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/templates")
def list_templates():
    return {
        "models": [
            {"id": "model3", "label": "Model 3", "description": "Sedan"},
            {"id": "modely", "label": "Model Y", "description": "SUV / Crossover"},
        ]
    }
