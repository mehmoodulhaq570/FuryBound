"use client";

import { motion } from "motion/react";

import { DragonSilhouette } from "@/components/art/dragon-silhouette";

export type StagePhase = "circling" | "peel";

const ORBIT_PX = 96;
// Where the runners-up fly off to, left and right.
const AWAY = [
  { x: -480, y: -260, rotate: -35 },
  { x: 480, y: -260, rotate: 35 },
];

/**
 * The top three circle overhead, then the runners-up peel away and the chosen one dives
 * toward the player. Each is drawn in its own species' shape.
 */
export function RevealStage({
  phase,
  chosen,
  others,
}: {
  phase: StagePhase;
  chosen: string;
  others: string[];
}) {
  const circling = [chosen, ...others];
  return (
    <div aria-hidden="true" className="relative mx-auto h-72 w-full max-w-md overflow-hidden">
      {phase === "circling" ? (
        <motion.div
          className="absolute inset-0"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, ease: "linear", repeat: Infinity }}
        >
          {circling.map((speciesId, i) => (
            <div
              key={speciesId}
              className="text-foreground absolute top-1/2 left-1/2 opacity-70"
              style={{
                transform: `translate(-50%, -50%) rotate(${(i * 360) / circling.length}deg) translateY(-${ORBIT_PX}px) rotate(-90deg)`,
              }}
            >
              <DragonSilhouette speciesId={speciesId} className="w-16" />
            </div>
          ))}
        </motion.div>
      ) : (
        <>
          {others.slice(0, AWAY.length).map((speciesId, i) => (
            <motion.div
              key={speciesId}
              className="text-foreground absolute top-1/2 left-1/2 -mt-8 -ml-8 w-16"
              initial={{ x: i === 0 ? -120 : 120, y: -70, rotate: 0, opacity: 0.7 }}
              animate={{ ...AWAY[i], opacity: 0 }}
              transition={{ duration: 1.2, ease: "easeInOut" }}
            >
              <DragonSilhouette speciesId={speciesId} />
            </motion.div>
          ))}
          <motion.div
            className="text-accent absolute top-1/2 left-1/2 -mt-8 -ml-8 w-16"
            initial={{ x: 0, y: -70, scale: 1, opacity: 0.7 }}
            animate={{ x: 0, y: 20, scale: 2.2, opacity: 1 }}
            transition={{ duration: 1.2, ease: "easeInOut", delay: 0.3 }}
          >
            <DragonSilhouette speciesId={chosen} />
          </motion.div>
        </>
      )}
    </div>
  );
}
