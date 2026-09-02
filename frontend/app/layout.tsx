import type { Metadata } from "next";
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
      <body>{children}</body>
    </html>
  );
}
