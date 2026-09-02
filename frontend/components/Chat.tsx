"use client";

import { useEffect, useRef, useState } from "react";

import {
  ApiError,
  getConversationHistory,
  sendChatMessage,
  type ChatSource,
  type Role,
} from "@/lib/api";

const STORAGE_KEY = "tradecopilot.conversation_id";

const EXAMPLES = [
  "Analyze BTCUSDT on the 15m timeframe.",
  "What about the FVG?",
  "Where is liquidity?",
  "Explain CHoCH.",
];

interface UiMessage {
  role: Role;
  content: string;
  sources?: ChatSource[];
  error?: boolean;
}

export default function Chat() {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Restore the previous conversation on mount.
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;

    setConversationId(stored);

    getConversationHistory(stored)
      .then((history) => {
        setMessages(
          history.messages.map((message) => ({
            role: message.role,
            content: message.content,
          })),
        );
      })
      .catch((error) => {
        // A stale id (e.g. the backend DB was reset) should not block the UI.
        if (error instanceof ApiError && error.status === 404) {
          localStorage.removeItem(STORAGE_KEY);
          setConversationId(null);
        }
      });
  }, []);

  // Keep the newest message in view.
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending]);

  async function submit(text: string) {
    const question = text.trim();
    if (!question || pending) return;

    setInput("");
    setPending(true);
    setMessages((current) => [
      ...current,
      { role: "user", content: question },
    ]);

    try {
      const result = await sendChatMessage(question, conversationId);

      if (result.conversation_id !== conversationId) {
        setConversationId(result.conversation_id);
        localStorage.setItem(STORAGE_KEY, result.conversation_id);
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources,
        },
      ]);
    } catch (error) {
      const detail =
        error instanceof ApiError
          ? error.message
          : "Something went wrong. Please try again.";

      setMessages((current) => [
        ...current,
        { role: "assistant", content: detail, error: true },
      ]);
    } finally {
      setPending(false);
      textareaRef.current?.focus();
    }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter inserts a newline.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(input);
    }
  }

  function newConversation() {
    localStorage.removeItem(STORAGE_KEY);
    setConversationId(null);
    setMessages([]);
    textareaRef.current?.focus();
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="dot" />
          Trade Copilot
          <span className="sub">market analysis + knowledge base</span>
        </div>

        {messages.length > 0 && (
          <button className="reset-btn" onClick={newConversation}>
            New chat
          </button>
        )}
      </header>

      <div className="messages" ref={scrollRef}>
        {messages.length === 0 && !pending ? (
          <div className="empty">
            <h2>Ask about the market</h2>
            <p>
              Live analysis comes from the deterministic engine. Trading
              concepts come from the knowledge base.
            </p>

            <div className="examples">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  className="example"
                  onClick={() => submit(example)}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div className={`msg ${message.role}`} key={index}>
              <span className="role">
                {message.role === "user" ? "You" : "Copilot"}
              </span>

              <div
                className={`bubble${message.error ? " error" : ""}`}
              >
                {message.content}
              </div>

              {message.sources && message.sources.length > 0 && (
                <details className="sources">
                  <summary>
                    {message.sources.length} knowledge-base source
                    {message.sources.length === 1 ? "" : "s"}
                  </summary>

                  {message.sources.map((source, sourceIndex) => (
                    <div className="source" key={sourceIndex}>
                      <div className="cite">
                        [{source.source}
                        {source.page != null ? `, p. ${source.page}` : ""}]
                        {source.score != null
                          ? ` · score ${source.score.toFixed(3)}`
                          : ""}
                      </div>
                      <div className="snippet">{source.text}</div>
                    </div>
                  ))}
                </details>
              )}
            </div>
          ))
        )}

        {pending && (
          <div className="msg assistant">
            <span className="role">Copilot</span>
            <div className="bubble pending">Analyzing market…</div>
          </div>
        )}
      </div>

      <div className="composer">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          placeholder="Analyze BTCUSDT on the 15m timeframe…"
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={onKeyDown}
          disabled={pending}
        />
        <button onClick={() => submit(input)} disabled={pending || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
