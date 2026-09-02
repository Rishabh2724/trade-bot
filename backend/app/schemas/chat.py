from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------
# Chat request
# ---------------------------------------

class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message / question for the copilot.",
        examples=["Analyze BTCUSDT on the 15m timeframe."],
    )

    conversation_id: str | None = Field(
        default=None,
        description=(
            "Existing conversation id. Omit to start a new "
            "conversation; the response returns the new id."
        ),
    )


# ---------------------------------------
# Knowledge-base source cited in an answer
# ---------------------------------------

class ChatSource(BaseModel):

    text: str = ""

    source: str = "Unknown"

    # Pinecone stores page as an int, but ingestion may leave it as the
    # literal "Unknown", so accept both.
    page: int | str | None = None

    score: float | None = None


# ---------------------------------------
# Chat response
# ---------------------------------------

class ChatResponse(BaseModel):

    conversation_id: str = Field(
        ...,
        description="Conversation id to reuse for follow-up messages.",
    )

    answer: str

    sources: list[ChatSource] = Field(
        default_factory=list,
        description="Knowledge-base passages used to ground the answer.",
    )


# ---------------------------------------
# Stored conversation message
# ---------------------------------------

class ChatMessage(BaseModel):

    role: Literal["user", "assistant"]

    content: str

    created_at: str | None = Field(
        default=None,
        description="UTC timestamp assigned by SQLite when stored.",
    )


# ---------------------------------------
# Full conversation history
# ---------------------------------------

class ConversationHistoryResponse(BaseModel):

    conversation_id: str

    message_count: int = Field(
        ...,
        description="Total number of stored messages.",
    )

    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="Complete conversation in chronological order.",
    )
