export const NAME_LENGTH = { min: 2, max: 20 } as const;

/**
 * A quick check before sending, so obvious mistakes show at once. The API has the final
 * say (it also filters unkind names).
 */
export function nameProblem(raw: string): string | null {
  const name = raw.trim().replace(/\s+/g, " ");
  if (name.length < NAME_LENGTH.min || name.length > NAME_LENGTH.max) {
    return `Names are ${NAME_LENGTH.min} to ${NAME_LENGTH.max} characters long`;
  }
  if (!/^\p{L}+(?:[ '-]\p{L}+)*$/u.test(name)) {
    return "Use letters, with single spaces, hyphens or apostrophes between them";
  }
  return null;
}
