import type { components } from "@/lib/api/schema";

export type ChatMessage = components["schemas"]["ChatMessage"];
// The stream's events. OpenAPI can't describe what's inside a stream, so these mirror
// StreamDelta and StreamDone in apps/api/app/schemas/chat.py by hand.
export type ChatEvent =
  { type: "delta"; text: string } | { type: "done"; message: ChatMessage; fallback: boolean };

/**
 * Reads server-sent events from a stream in whatever chunks they arrive: an event ends with
 * a blank line, and its JSON follows "data: ".
 */
export function sseReader(onEvent: (event: ChatEvent) => void) {
  let buffer = "";
  return (chunk: string) => {
    buffer += chunk.replace(/\r\n/g, "\n");
    let end: number;
    while ((end = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data: "))
        .map((line) => line.slice(6))
        .join("\n");
      if (data) onEvent(JSON.parse(data) as ChatEvent);
    }
  };
}

export type ReplyPart = { kind: "action" | "thought" | "text"; text: string };

/**
 * A narrated reply's parts: *what the dragon does* (action) and "💭 ..." (thought).
 * Anything else stays plain text, so an off-format reply still shows.
 */
export function replyParts(reply: string): ReplyPart[] {
  return reply
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line): ReplyPart => {
      if (line.startsWith("💭")) return { kind: "thought", text: line.slice(2).trim() };
      const action = /^\*(.+)\*$/.exec(line);
      if (action) return { kind: "action", text: action[1].trim() };
      return { kind: "text", text: line };
    });
}
