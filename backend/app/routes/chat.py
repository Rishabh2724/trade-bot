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
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.rag_chain import ask_trade_copilot
from app.services.chat_history import (
    create_conversation,
    conversation_exists,
    add_message,
)


router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)


# ---------------------------------------
# Request
# ---------------------------------------

class ChatRequest(BaseModel):

    message: str

    conversation_id: str | None = None


# ---------------------------------------
# Chat
# ---------------------------------------

@router.post("/chat")
def chat(request: ChatRequest):

    try:

        # Create a new conversation if
        # the client did not provide one.

        conversation_id = request.conversation_id

        if conversation_id is None:

            conversation_id = create_conversation()

        elif not conversation_exists(conversation_id):

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # Save user message

        add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        # Generate response

        result = ask_trade_copilot(
            question=request.message,
            conversation_id=conversation_id,
        )

        # Save assistant response

        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
        )

        return {
            "conversation_id": conversation_id,
            "answer": result["answer"],
            "sources": result["sources"],
        }

    except HTTPException:
        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(error)}",
        )
