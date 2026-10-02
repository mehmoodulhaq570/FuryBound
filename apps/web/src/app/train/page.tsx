import type { Metadata } from "next";

import { TrainHome } from "@/components/training/train-home";

export const metadata: Metadata = { title: "Training · Dragon Academy" };

export default function TrainPage() {
  return <TrainHome />;
}
