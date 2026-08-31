from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.rag_chain import ask_trade_copilot


router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest):

    result = ask_trade_copilot(
        request.message
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }