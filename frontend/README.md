# Trade Copilot — Frontend

Next.js (App Router) + TypeScript chat UI for the Trade Copilot API.

## Setup

```bash
npm install
cp .env.local.example .env.local
```

`NEXT_PUBLIC_API_BASE_URL` must point at the FastAPI backend
(default `http://localhost:8000`).

## Run

Start the backend first, from `../backend`:

```bash
uvicorn app.main:app --reload
```

Then the frontend:

```bash
npm run dev
```

Open http://localhost:3000.

The backend allows `http://localhost:3000` via CORS by default. Override
with the `FRONTEND_ORIGINS` env var (comma-separated origins) when
deploying.

## Structure

```text
app/
  layout.tsx      Root layout
  page.tsx        Renders <Chat />
  globals.css     Dark trading theme
components/
  Chat.tsx        Chat UI: messages, sources, composer
lib/
  api.ts          Typed client; mirrors backend/app/schemas/chat.py
```

## Behaviour

- `conversation_id` is persisted in `localStorage`, so a reload resumes
  the same conversation via `GET /api/chat/{id}/history`. A stale id
  (404) is cleared automatically.
- Follow-up questions rely on the backend's conversational market
  context, so "what about the FVG?" stays on the previously analyzed
  symbol and timeframe.
- Knowledge-base citations are collapsed under each answer.
- Enter sends; Shift+Enter inserts a newline.
