"use client";

import { useState } from "react";

import { DragonActor } from "@/components/art/dragon-actor";

export function RescueInteraction({
  method,
  pending,
  onComplete,
}: {
  method: "untie" | "lift";
  pending: boolean;
  onComplete: () => void;
}) {
  const [loosened, setLoosened] = useState<number[]>([]);
  const [lift, setLift] = useState(0);
  const ready = method === "untie" ? loosened.length === 3 : lift === 3;
  return (
    <div className="space-y-4">
      <div className="relative h-64 overflow-hidden rounded-3xl bg-gradient-to-b from-slate-400 via-teal-700 to-teal-950">
        <div className="absolute right-8 bottom-4 w-52">
          <DragonActor speciesId="scuttleclaw" color="#9eb879" pose={ready ? "happy" : "idle"} />
        </div>
        <div
          className="absolute right-8 bottom-12 h-28 w-44 rounded-2xl border-2 border-amber-100/70 transition-transform"
          aria-hidden="true"
          style={{
            opacity: ready ? 0 : 1,
            transform: `translateY(-${lift * 25}px)`,
            backgroundImage:
              "repeating-linear-gradient(45deg, transparent 0 15px, #ffecc366 16px 18px), repeating-linear-gradient(-45deg, transparent 0 15px, #ffecc366 16px 18px)",
          }}
        />
        {method === "untie" &&
          [0, 1, 2].map(
            (knot) =>
              !loosened.includes(knot) && (
                <button
                  type="button"
                  key={knot}
                  disabled={pending}
                  aria-label={`Loosen knot ${knot + 1}`}
                  className="absolute z-10 flex size-12 items-center justify-center rounded-full border-2 border-amber-100 bg-amber-700 text-xl text-amber-100 shadow-lg"
                  style={{ right: `${10 + knot * 14}%`, bottom: `${30 + (knot % 2) * 18}%` }}
                  onClick={() =>
                    setLoosened((current) =>
                      current.includes(knot) ? current : [...current, knot],
                    )
                  }
                >
                  ∞
                </button>
              ),
          )}
      </div>
      <p role="status">
        {ready
          ? "The net is clear. Help the little dragon back to the shore."
          : method === "untie"
            ? `${loosened.length}/3 knots loosened. Tap each knot on the net.`
            : `${lift}/3 lifts. Work together to raise the net.`}
      </p>
      {method === "lift" && !ready && (
        <button
          type="button"
          className="bg-accent rounded-xl px-5 py-3 text-white"
          onClick={() => setLift((current) => Math.min(3, current + 1))}
        >
          Lift together
        </button>
      )}
      {ready && (
        <button
          type="button"
          className="bg-accent rounded-xl px-5 py-3 text-white disabled:opacity-50"
          disabled={pending}
          onClick={onComplete}
        >
          {pending ? "Saving your rescue…" : "Guide the dragon to safety"}
        </button>
      )}
    </div>
  );
}
