import type { Metadata } from "next";

import { AdventureHome } from "@/components/experience/adventure-home";

export const metadata: Metadata = { title: "Misty Cove rescue · Dragon Academy" };

export default function AdventurePage() {
  return <AdventureHome />;
}
