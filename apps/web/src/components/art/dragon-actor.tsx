import type { CSSProperties } from "react";

import styles from "./dragon-actor.module.css";

export type DragonPose = "idle" | "walk" | "eat" | "sleep" | "happy" | "fly" | "land" | "takeoff";

/** Original side-view puppet. Species anatomy is independent of the flight silhouettes. */
export function DragonActor({
  speciesId,
  color = "#426d79",
  pose = "idle",
  mood = "happy",
}: {
  speciesId: string;
  color?: string | null;
  pose?: DragonPose;
  mood?: string;
}) {
  const round = ["gronckle", "hotburple", "hobgobbler", "snafflefang"].includes(speciesId);
  const fury = speciesId === "night_fury" || speciesId === "light_fury";
  const twin = speciesId === "hideous_zippleback";
  const doubleWings = speciesId === "stormcutter";
  const sixLegs = speciesId === "deathgripper";
  const horns = [
    "stormcutter",
    "crimson_goregutter",
    "monstrous_nightmare",
    "scuttleclaw",
  ].includes(speciesId);
  const spikes = ["deadly_nadder", "scuttleclaw", "deathgripper"].includes(speciesId);
  const body = round
    ? "M76 95C76 47 171 41 182 100C195 153 65 160 76 95Z"
    : "M75 104C96 68 152 70 177 101C191 132 95 150 75 104Z";
  const head = (second = false) => (
    <g transform={second ? "translate(-8 -34) scale(.93)" : undefined}>
      <g className={styles.head}>
        <path
          d={
            round
              ? "M163 109Q173 69 195 67L203 94L186 122Z"
              : "M155 112Q170 97 182 63L207 68Q197 114 177 128Z"
          }
        />
        {horns && <path className={styles.horn} d="M192 58Q182 34 202 29L199 58Z" />}
        {speciesId === "rumblehorn" && <path className={styles.horn} d="M242 65L260 41L253 83Z" />}
        {speciesId === "deadly_nadder" && (
          <path className={styles.horn} d="M185 64L178 40L201 54L199 33L215 53L226 37L226 64Z" />
        )}
        {fury && <path d="M192 59L182 43Q201 40 208 58M212 56L215 42Q233 45 225 67" />}
        <path
          d={
            round
              ? "M180 65Q205 46 230 66L253 83Q262 106 227 112L192 103Z"
              : "M181 68Q187 48 214 58Q234 63 242 77L255 82Q262 96 237 102L190 95Z"
          }
        />
        {speciesId === "snafflefang" && (
          <path className={styles.horn} d="M236 97L245 117L247 98Z" />
        )}
        {sixLegs && <path className={styles.horn} d="M246 89Q267 94 263 111L256 99L243 99Z" />}
        <path className={styles.cheek} d="M194 88Q208 99 225 99Q220 112 200 105Z" />
        <g className={styles.eye}>
          <ellipse
            cx="220"
            cy="76"
            rx="9"
            ry="10"
            fill={speciesId === "light_fury" ? "#80d1e4" : "#f4cc69"}
          />
          <ellipse cx="223" cy="77" rx="3" ry="8" fill="#142c31" />
          <circle cx="224" cy="72" r="2" fill="#fff" />
        </g>
        <path className={styles.lid} d="M212 76Q220 84 229 76" />
        <path d="M244 85l3 1" stroke="#18353b" strokeWidth="3" strokeLinecap="round" />
        <path className={styles.mouth} d="M231 96Q242 99 252 92" />
        {mood === "angry" && <path d="M210 65l17 6" stroke="#18353b" strokeWidth="4" />}
      </g>
    </g>
  );
  return (
    <svg
      viewBox="0 0 280 190"
      aria-hidden="true"
      data-species={speciesId}
      data-pose={pose}
      className={`${styles.actor} ${styles[pose]} ${mood === "tired" ? styles.drowsy : ""} ${mood === "curious" ? styles.curious : ""}`}
      style={{ "--skin": color ?? "#426d79" } as CSSProperties}
    >
      <ellipse className={styles.shadow} cx="143" cy="163" rx="87" ry="9" />
      <g className={styles.puppet}>
        <g className={styles.tail}>
          <path
            d={
              round
                ? "M91 112Q46 133 24 109Q27 151 105 130Z"
                : "M98 110Q52 138 13 87Q16 144 104 132Z"
            }
          />
          {speciesId === "gronckle" && <ellipse cx="24" cy="110" rx="16" ry="13" />}
          {fury && <path d="M28 118L7 104L12 126L36 133Z" />}
          {sixLegs && <path className={styles.horn} d="M19 112L3 91L3 117L21 128Z" />}
          {twin && <path d="M96 121Q52 152 20 134Q44 170 102 139Z" />}
          {spikes && (
            <path className={styles.horn} d="M38 125L33 112L48 128L55 117L65 132L75 122L84 135Z" />
          )}
        </g>
        <g className={styles.backLeg}>
          <path d="M117 120L100 150L119 159L90 160Q82 151 98 122Z" />
        </g>
        <g className={styles.frontLeg}>
          <path d="M161 115L164 148L181 155L152 158L144 123Z" />
        </g>
        {sixLegs && (
          <g className={styles.middleLeg}>
            <path d="M130 119L119 145L135 155L112 154L113 126Z" />
          </g>
        )}
        <path d={body} />
        <path className={styles.belly} d="M97 119Q138 134 175 107Q182 141 125 142Z" />
        {spikes && (
          <path
            className={styles.horn}
            d="M88 89L90 75L102 81L112 66L123 77L139 63L143 78L163 72L166 91Z"
          />
        )}
        <g className={styles.wing}>
          <path
            d={
              round
                ? "M119 95Q106 56 79 54Q90 88 119 110Z"
                : "M127 91Q97 36 45 33L62 67Q86 54 91 89Q111 77 127 111Z"
            }
          />
          <path className={styles.wingVein} d="M124 96Q92 69 54 40M92 70L94 87" />
        </g>
        {doubleWings && (
          <g className={styles.secondWing}>
            <path d="M132 112Q102 81 62 86L79 113Q103 105 132 127Z" />
          </g>
        )}
        <g className={styles.backLeg}>
          <path d="M112 125L108 150L129 158L98 160L91 134Z" />
        </g>
        <g className={styles.frontLeg}>
          <path d="M163 116L177 147L198 155L167 158L148 127Z" />
        </g>
        {sixLegs && (
          <g className={styles.middleLeg}>
            <path d="M137 123L133 151L151 158L124 161L119 131Z" />
          </g>
        )}
        {head()}
        {twin && head(true)}
        <g className={styles.sparkles} fill="#ffe39a">
          <path d="M214 25l3 7 7 3-7 3-3 7-3-7-7-3 7-3ZM253 45l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" />
        </g>
      </g>
    </svg>
  );
}
