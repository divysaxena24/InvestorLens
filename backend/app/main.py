
from fastapi import FastAPI

app = FastAPI(
    title="InvestorLens API",
    description="AI-powered financial research and intelligence platform",
    version="0.1.0",
)


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
