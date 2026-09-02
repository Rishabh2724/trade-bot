from fastapi import APIRouter, HTTPException

from app.rag.rag_chain import ask_trade_copilot
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from app.schemas.common import (
    RESPONSE_400,
    RESPONSE_404,
    RESPONSE_500,
    RESPONSE_502,
)
from app.services.chat_history import (
    create_conversation,
    conversation_exists,
    add_message,
    get_all_messages,
)


router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)


# ---------------------------------------
# Chat
# ---------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the trading copilot",
    responses={
        400: RESPONSE_400,
        404: RESPONSE_404,
        502: RESPONSE_502,
        500: RESPONSE_500,
    },
)
def chat(request: ChatRequest) -> ChatResponse:

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

        return ChatResponse(
            conversation_id=conversation_id,
            answer=result["answer"],
            sources=result["sources"],
        )

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
# Get full conversation history
# ---------------------------------------

@router.get(
    "/chat/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
    summary="Get the full stored conversation",
    responses={
        404: RESPONSE_404,
        500: RESPONSE_500,
    },
)
def get_chat_history(
    conversation_id: str,
) -> ConversationHistoryResponse:

    try:

        if not conversation_exists(conversation_id):

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # Full conversation, not the LLM-capped window.
        messages = get_all_messages(conversation_id)

        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            message_count=len(messages),
            messages=messages,
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chat history: {str(error)}",
        )
