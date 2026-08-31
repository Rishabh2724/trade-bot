from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.markets import router as market_router
from app.routes.analysis import router as analysis_router

app = FastAPI(
    title="TradeCopilot API",
    version="1.0.0",
)


# ---------------------------------------
# API Routers
# ---------------------------------------

app.include_router(
    chat_router
)

app.include_router(
    market_router
)

app.include_router(
    analysis_router
)


# ---------------------------------------
# Root
# ---------------------------------------

@app.get("/")
def root():

    return {
        "message": "TradeCopilot API is running"
    }


# ---------------------------------------
# Health
# ---------------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }