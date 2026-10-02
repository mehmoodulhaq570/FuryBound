import type { Metadata } from "next";

import { AcademyBook } from "@/components/dragon-book/academy-book";
import { dragons, movies, toCard } from "@/lib/dragon-book/catalog";

export const metadata: Metadata = {
  title: "Dragon Book · Dragon Academy",
  description: "Every dragon in the three How to Train Your Dragon films, with sources.",
};

export default function DragonBookPage() {
  const cards = dragons.map(toCard);
  const species = cards.filter((c) => c.kind === "species").length;

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <p className="text-accent text-sm font-medium tracking-widest uppercase">Dragon Book</p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Every dragon in the films
        </h1>
        <p className="text-muted max-w-prose">
          {species} species and {cards.length - species} named dragons from the three films. Each
          entry shows which films it appears in and how sure we are. Much of this is still being
          checked against the films, so look for the confidence dots.
        </p>
      </header>
      <AcademyBook cards={cards} movies={movies} />
    </div>
  );
}
