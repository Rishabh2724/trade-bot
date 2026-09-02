import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.markets import router as market_router
from app.routes.analysis import router as analysis_router
from app.services.chat_history import init_chat_history

app = FastAPI(
    title="TradeCopilot API",
    version="1.0.0",
)

init_chat_history()

# ---------------------------------------
# CORS
# ---------------------------------------
# Allow the frontend dev server (and any deployed origins) to call the
# API from the browser. Override in production via FRONTEND_ORIGINS
# (comma-separated list of origins).

_default_origins = "http://localhost:3000,http://127.0.0.1:3000"

allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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