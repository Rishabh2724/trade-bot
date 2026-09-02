import { Suspense } from "react";

import Chat from "@/components/Chat";

export default function ChatPage() {
  return (
    // Chat reads ?q= to accept a question handed over from the dashboard.
    <Suspense fallback={<Loading />}>
      <Chat />
    </Suspense>
  );
}

function Loading() {
  return (
    <div className="grid h-full place-items-center text-xs text-muted">
      Loading chat…
    </div>
  );
}
