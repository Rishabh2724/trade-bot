"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

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

  // The handed-over ?q= must wait for history to load, otherwise it would
  // start a brand-new conversation while the old one is still being restored.
  const [restored, setRestored] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const router = useRouter();
  const handoff = useSearchParams().get("q");

  // Restore the previous conversation on mount.
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      setRestored(true);
      return;
    }

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
      })
      .finally(() => setRestored(true));
  }, []);

  // Keep the newest message in view.
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending]);

  const submit = useCallback(
    async (text: string) => {
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
    },
    [conversationId, pending],
  );

  // Send a question deep-linked from the dashboard, exactly once.
  const sent = useRef(false);

  useEffect(() => {
    if (!restored || !handoff || sent.current) return;

    sent.current = true;
    submit(handoff);

    // Drop ?q= so a reload does not ask the same question again.
    router.replace("/chat", { scroll: false });
  }, [restored, handoff, submit, router]);

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
    <div className="mx-auto flex h-full min-h-0 max-w-3xl flex-col">
      {messages.length > 0 ? (
        <div className="flex shrink-0 justify-end px-4 pt-3">
          <button
            type="button"
            onClick={newConversation}
            className="rounded-md border border-line px-2 py-1 text-[11px] text-muted transition-colors hover:border-accent hover:text-accent"
          >
            New chat
          </button>
        </div>
      ) : null}

      <div
        ref={scrollRef}
        className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4"
      >
        {messages.length === 0 && !pending ? (
          <div className="m-auto max-w-md text-center">
            <h2 className="text-base font-semibold text-ink">
              Ask about the market
            </h2>
            <p className="mt-1.5 text-xs leading-relaxed text-muted">
              Live analysis comes from the deterministic engine. Trading
              concepts come from the knowledge base.
            </p>

            <div className="mt-4 flex flex-wrap justify-center gap-1.5">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => submit(example)}
                  className="rounded-full border border-line px-2.5 py-1 text-[11px] text-muted transition-colors hover:border-accent hover:text-accent"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex flex-col gap-1 ${
                message.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <span className="text-[10px] tracking-wider text-muted uppercase">
                {message.role === "user" ? "You" : "Copilot"}
              </span>

              <div
                className={`max-w-[85%] rounded-panel px-3 py-2 text-[13px] leading-relaxed whitespace-pre-wrap ${
                  message.error
                    ? "border border-danger/40 bg-danger/10 text-danger"
                    : message.role === "user"
                      ? "bg-user text-white"
                      : "border border-line bg-panel text-ink"
                }`}
              >
                {message.content}
              </div>

              {message.sources && message.sources.length > 0 ? (
                <details className="max-w-[85%] text-[11px] text-muted">
                  <summary className="cursor-pointer py-1 hover:text-ink">
                    {message.sources.length} knowledge-base source
                    {message.sources.length === 1 ? "" : "s"}
                  </summary>

                  <div className="mt-1 flex flex-col gap-2">
                    {message.sources.map((source, sourceIndex) => (
                      <div
                        key={sourceIndex}
                        className="rounded-md border border-line bg-panel p-2"
                      >
                        <div className="font-mono text-[10px] text-accent">
                          [{source.source}
                          {source.page != null ? `, p. ${source.page}` : ""}]
                          {source.score != null
                            ? ` · score ${source.score.toFixed(3)}`
                            : ""}
                        </div>
                        <div className="mt-1 leading-relaxed text-muted">
                          {source.text}
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              ) : null}
            </div>
          ))
        )}

        {pending ? (
          <div className="flex flex-col items-start gap-1">
            <span className="text-[10px] tracking-wider text-muted uppercase">
              Copilot
            </span>
            <div className="rounded-panel border border-line bg-panel px-3 py-2 text-[13px] text-muted">
              Analyzing market…
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex shrink-0 items-end gap-2 border-t border-line bg-panel p-3">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          placeholder="Analyze BTCUSDT on the 15m timeframe…"
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={onKeyDown}
          disabled={pending}
          className="max-h-32 min-h-9 flex-1 resize-y rounded-md border border-line bg-panel-2 px-3 py-2 text-[13px] text-ink outline-none placeholder:text-muted/60 focus-visible:border-accent disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => submit(input)}
          disabled={pending || !input.trim()}
          className="h-9 rounded-md bg-accent px-4 text-[13px] font-semibold text-bg transition-opacity disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
