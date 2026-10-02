"use client";

import { motion } from "motion/react";

import { Silhouette } from "./silhouette";

export type StagePhase = "circling" | "peel";

const ORBIT_PX = 96;
// Once they line up, the chosen dragon is in the middle and the runners-up fly off either side.
const LINE_UP = [
  { x: -120, away: { x: -480, y: -260, rotate: -35 } },
  { x: 0, away: null },
  { x: 120, away: { x: 480, y: -260, rotate: 35 } },
];

/** Three silhouettes circle overhead, then two peel away and one dives toward the player. */
export function RevealStage({ phase }: { phase: StagePhase }) {
  return (
    <div aria-hidden="true" className="relative mx-auto h-72 w-full max-w-md overflow-hidden">
      {phase === "circling" ? (
        <motion.div
          className="absolute inset-0"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, ease: "linear", repeat: Infinity }}
        >
          {[0, 120, 240].map((angle, i) => (
            <div
              key={angle}
              className="text-foreground absolute top-1/2 left-1/2 opacity-70"
              style={{
                transform: `translate(-50%, -50%) rotate(${angle}deg) translateY(-${ORBIT_PX}px) rotate(-90deg)`,
              }}
            >
              <Silhouette className={i === 0 ? "w-16" : "w-12"} />
            </div>
          ))}
        </motion.div>
      ) : (
        LINE_UP.map(({ x, away }, i) => (
          <motion.div
            key={i}
            className={`absolute top-1/2 left-1/2 -mt-6 -ml-8 w-16 ${
              away ? "text-foreground" : "text-accent"
            }`}
            initial={{ x, y: -70, rotate: 0, scale: 1, opacity: 0.7 }}
            animate={away ? { ...away, opacity: 0 } : { x: 0, y: 30, scale: 2.2, opacity: 1 }}
            transition={{ duration: 1.2, ease: "easeInOut", delay: away ? 0 : 0.3 }}
          >
            <Silhouette />
          </motion.div>
        ))
      )}
    </div>
  );
}
