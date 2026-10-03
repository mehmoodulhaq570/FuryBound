import type { Metadata } from "next";

import { IslandHome } from "@/components/experience/island-home";

export const metadata: Metadata = { title: "Your island · Dragon Academy" };

export default function IslandPage() {
  return <IslandHome />;
}
