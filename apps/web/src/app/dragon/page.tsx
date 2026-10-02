import type { Metadata } from "next";

import { DragonHome } from "@/components/dragon/dragon-home";

export const metadata: Metadata = { title: "Your dragon · Dragon Academy" };

export default function DragonPage() {
  return <DragonHome />;
}
