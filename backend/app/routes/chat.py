from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.rag_chain import ask_trade_copilot
from app.services.chat_history import (
    create_conversation,
    conversation_exists,
    add_message,
    get_messages,
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

        # ---------------------------------------
        # Conversation
        # ---------------------------------------

        conversation_id = request.conversation_id

        if conversation_id is None:

            conversation_id = create_conversation()

        elif not conversation_exists(conversation_id):

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # ---------------------------------------
        # Save user message
        # ---------------------------------------

        add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        # ---------------------------------------
        # Generate response
        # ---------------------------------------

        result = ask_trade_copilot(
            question=request.message,
            conversation_id=conversation_id,
        )

        # ---------------------------------------
        # Save assistant response
        # ---------------------------------------

        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
        )

        # ---------------------------------------
        # Response
        # ---------------------------------------

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


# ---------------------------------------
# Get conversation history
# ---------------------------------------

@router.get("/chat/{conversation_id}")
def get_chat_history(conversation_id: str):

    try:

        if not conversation_exists(conversation_id):

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        messages = get_messages(
            conversation_id
        )

        return {
            "conversation_id": conversation_id,
            "messages": messages,
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chat history: {str(error)}",
        )