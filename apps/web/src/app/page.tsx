import Link from "next/link";

import { SystemCheck } from "@/components/system-check";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <p className="text-accent text-sm font-medium tracking-widest uppercase">Phase 3</p>
        <h1 className="text-4xl font-semibold tracking-tight">Dragon Academy</h1>
        <p className="text-muted max-w-prose">
          The dragon chooses you. Take the quiz, meet your dragon, train it, talk to it and go on
          adventures together. The quiz is open; the encounter and your dragon are coming next.
        </p>
      </section>
      <Link
        href="/academy/quiz"
        className="border-accent bg-surface block rounded-xl border p-5 transition-colors"
      >
        <h2 className="text-lg font-semibold">Find your dragon →</h2>
        <p className="text-muted text-sm">
          Twelve questions about how you&apos;d handle life at the Academy. Takes about two minutes.
        </p>
      </Link>
      <Link
        href="/dragon-book"
        className="border-line bg-surface hover:border-accent block rounded-xl border p-5 transition-colors"
      >
        <h2 className="text-lg font-semibold">Open the Dragon Book →</h2>
        <p className="text-muted text-sm">
          Every species and named dragon from the three films, with where each one appears.
        </p>
      </Link>
      <SystemCheck />
    </div>
  );
}
