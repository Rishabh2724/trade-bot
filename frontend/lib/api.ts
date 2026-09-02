// Typed client for the TradeCopilot FastAPI backend.
// Types mirror backend/app/schemas/chat.py.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ---------------------------------------
// Types
// ---------------------------------------

export type Role = "user" | "assistant";

export interface ChatSource {
  text: string;
  source: string;
  page: number | string | null;
  score: number | null;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: ChatSource[];
}

export interface ChatMessage {
  role: Role;
  content: string;
  created_at: string | null;
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  message_count: number;
  messages: ChatMessage[];
}

// Error body from the backend (schemas/common.py ErrorResponse).
export class ApiError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
  }
}

// ---------------------------------------
// Internal helpers
// ---------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(
      0,
      "Could not reach the API. Is the backend running?",
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON error body; keep the generic message.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

// ---------------------------------------
// Endpoints
// ---------------------------------------

export function sendChatMessage(
  message: string,
  conversationId: string | null,
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
}

export function getConversationHistory(
  conversationId: string,
): Promise<ConversationHistoryResponse> {
  return request<ConversationHistoryResponse>(
    `/api/chat/${encodeURIComponent(conversationId)}/history`,
  );
}
