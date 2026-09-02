import type { Metadata } from "next";
import { Suspense } from "react";

import Sidebar from "@/components/shell/Sidebar";
import TopBar from "@/components/shell/TopBar";

import "./globals.css";

export const metadata: Metadata = {
  title: "Trade Copilot",
  description: "AI-powered trading research and market-analysis assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      {/*
        h-dvh, not h-screen: on mobile Safari h-screen includes the area behind
        the browser chrome, which would push the composer off screen.
      */}
      <body className="flex h-dvh flex-col overflow-hidden">
        {/* TopBar reads useSearchParams, which Next requires a boundary for. */}
        <Suspense fallback={<TopBarFallback />}>
          <TopBar />
        </Suspense>

        <div className="flex min-h-0 flex-1">
          <Sidebar />
          <main className="min-h-0 min-w-0 flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}

/** Same height as the real bar so the layout does not jump on hydration. */
function TopBarFallback() {
  return (
    <div className="flex h-12 shrink-0 items-center gap-2 border-b border-line bg-panel px-3">
      <span aria-hidden className="h-2 w-2 rounded-full bg-accent" />
      <span className="text-[13px] font-bold tracking-[0.16em] text-ink">
        TRADECOPILOT
      </span>
    </div>
  );
}
