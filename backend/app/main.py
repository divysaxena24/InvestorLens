
from fastapi import FastAPI

from app.api.routes.documents import router as documents_router

app = FastAPI(
    title="InvestorLens API",
    description="AI-powered financial research and intelligence platform",
    version="0.1.0",
)

app.include_router(documents_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Welcome to InvestorLens API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "InvestorLens API",
        "version": "0.1.0",
    }
