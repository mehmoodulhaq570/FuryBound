import type { Metadata } from "next";

import { RevealFlow } from "@/components/reveal/reveal-flow";

export const metadata: Metadata = { title: "The dragon chooses you · Dragon Academy" };

export default async function RevealPage({
  searchParams,
}: {
  searchParams: Promise<{ attempt?: string | string[] }>;
}) {
  const { attempt } = await searchParams;
  return <RevealFlow attemptId={typeof attempt === "string" ? attempt : null} />;
}
