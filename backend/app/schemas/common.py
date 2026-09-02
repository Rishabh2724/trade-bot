from pydantic import BaseModel, Field


# ---------------------------------------
# Standard error envelope
# ---------------------------------------

class ErrorResponse(BaseModel):
    """Uniform error body returned by every endpoint via HTTPException."""

    detail: str = Field(
        ...,
        description="Human-readable explanation of the error.",
        examples=["Conversation not found"],
    )


# Reusable OpenAPI `responses=` fragments so Swagger documents the
# error bodies the frontend can expect.

RESPONSE_400 = {
    "model": ErrorResponse,
    "description": "Invalid request input.",
}

RESPONSE_404 = {
    "model": ErrorResponse,
    "description": "Requested resource does not exist.",
}

RESPONSE_502 = {
    "model": ErrorResponse,
    "description": "Upstream data provider failed.",
}

RESPONSE_500 = {
    "model": ErrorResponse,
    "description": "Unexpected server error.",
}
