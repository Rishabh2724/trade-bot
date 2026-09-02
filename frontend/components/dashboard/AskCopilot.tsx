"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * The mockup's "Ask TradeCopilot" input. Rather than duplicate the chat
 * transport here, it deep-links to /chat?q=… and the chat page submits the
 * question once on mount — one conversation store, one code path.
 */
export default function AskCopilot({ symbol }: { symbol: string }) {
  const router = useRouter();
  const [value, setValue] = useState("");

  function ask(question: string) {
    const text = question.trim();
    if (!text) return;

    router.push(`/chat?q=${encodeURIComponent(text)}`);
  }

  return (
    <section className="flex flex-col gap-2 border-t border-line pt-3">
      <span className="text-[10px] tracking-wider text-muted uppercase">
        Ask TradeCopilot
      </span>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask(value);
        }}
        className="flex gap-1.5"
      >
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={`What is the bias on ${symbol}?`}
          aria-label="Ask TradeCopilot a question"
          className="min-w-0 flex-1 rounded-md border border-line bg-panel-2 px-2 py-1.5 text-xs text-ink outline-none placeholder:text-muted/60 focus-visible:border-accent"
        />
        <button
          type="submit"
          disabled={!value.trim()}
          className="rounded-md bg-accent px-2.5 py-1.5 text-xs font-semibold text-bg disabled:opacity-40"
        >
          Ask
        </button>
      </form>

      <div className="flex flex-wrap gap-1">
        {[
          `Analyze ${symbol} structure.`,
          "Where is liquidity?",
          "Explain CHoCH.",
        ].map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => ask(example)}
            className="rounded-full border border-line px-2 py-0.5 text-[10px] text-muted transition-colors hover:border-accent hover:text-accent"
          >
            {example}
          </button>
        ))}
      </div>
    </section>
  );
}
