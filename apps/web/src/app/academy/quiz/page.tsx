import type { Metadata } from "next";

import { QuizFlow } from "@/components/quiz/quiz-flow";

export const metadata: Metadata = { title: "Personality quiz · Dragon Academy" };

export default function QuizPage() {
  return <QuizFlow />;
}
