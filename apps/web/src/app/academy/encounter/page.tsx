import type { Metadata } from "next";

import { EncounterFlow } from "@/components/encounter/encounter-flow";

export const metadata: Metadata = { title: "The encounter · Dragon Academy" };

export default async function EncounterPage({
  searchParams,
}: {
  searchParams: Promise<{ attempt?: string | string[] }>;
}) {
  const { attempt } = await searchParams;
  return <EncounterFlow attemptId={typeof attempt === "string" ? attempt : null} />;
}
