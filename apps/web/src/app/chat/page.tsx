import type { Metadata } from "next";

import { ChatPage } from "@/components/chat/chat-page";

export const metadata: Metadata = { title: "Talk to your dragon · Dragon Academy" };

export default function Page() {
  return <ChatPage />;
}
