from fastapi import FastAPI

from app.api.market import router as market_router


app = FastAPI(
    title="Electricity Trading Agent",
    description="AI-powered electricity trading decision system",
    version="0.1.0",
)


app.include_router(
    market_router,
    prefix="/api",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "electricity-trading-agent",
    }
