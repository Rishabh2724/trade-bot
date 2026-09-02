"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/*
 * Only Dashboard and TradeCopilot AI have anything behind them. The rest are
 * shown but disabled rather than hidden, so the roadmap is visible without
 * pretending the pages exist. Portfolio in particular is deliberately
 * deferred (section 26 of the project doc).
 */
const NAV = [
  { label: "Dashboard", href: "/", icon: "▤" },
  { label: "Market Analysis", href: null, icon: "◪" },
  { label: "TradeCopilot AI", href: "/chat", icon: "◆" },
  { label: "Portfolio", href: null, icon: "◫" },
  { label: "Knowledge Base", href: null, icon: "▦" },
  { label: "Settings", href: null, icon: "◇" },
] as const;

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      className="flex w-14 shrink-0 flex-col gap-1 border-r border-line bg-panel p-2 lg:w-52"
    >
      {NAV.map((item) => {
        if (!item.href) {
          return (
            <span
              key={item.label}
              aria-disabled="true"
              title={`${item.label} — not built yet`}
              className="flex cursor-not-allowed items-center gap-3 rounded-md px-2 py-2 text-sm text-muted/45 select-none"
            >
              <span aria-hidden className="w-4 text-center">
                {item.icon}
              </span>
              <span className="hidden truncate lg:inline">{item.label}</span>
              <span className="ml-auto hidden text-[9px] tracking-wider uppercase lg:inline">
                soon
              </span>
            </span>
          );
        }

        const active = pathname === item.href;

        return (
          <Link
            key={item.label}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors ${
              active
                ? "bg-panel-2 text-accent"
                : "text-ink/80 hover:bg-panel-2 hover:text-ink"
            }`}
          >
            <span aria-hidden className="w-4 text-center">
              {item.icon}
            </span>
            <span className="hidden truncate lg:inline">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
