import { describe, expect, it } from "vitest";

import { replyParts, sseReader, type ChatEvent } from "./parse";

describe("sseReader", () => {
  it("handles events split across chunks", () => {
    const events: ChatEvent[] = [];
    const feed = sseReader((e) => events.push(e));
    feed('data: {"type":"delta","te');
    feed('xt":"Hi "}\n\ndata: {"type":"delta","text":"there"}\n');
    expect(events).toEqual([{ type: "delta", text: "Hi " }]);
    feed("\n");
    expect(events.map((e) => e.type === "delta" && e.text)).toEqual(["Hi ", "there"]);
  });

  it("reads the final event", () => {
    const events: ChatEvent[] = [];
    const done = {
      type: "done",
      fallback: false,
      message: { id: 1, role: "dragon", content: "Hi", mode: "narrated", created_at: "x" },
    };
    sseReader((e) => events.push(e))(`data: ${JSON.stringify(done)}\r\n\r\n`);
    expect(events).toEqual([done]);
  });
});

describe("replyParts", () => {
  it("splits a narrated reply into what the dragon does and thinks", () => {
    expect(replyParts("*Ember nudges the basket.*\n💭 Fish. Now.")).toEqual([
      { kind: "action", text: "Ember nudges the basket." },
      { kind: "thought", text: "Fish. Now." },
    ]);
  });

  it("keeps anything else as text", () => {
    expect(replyParts("I love fish!\n\n")).toEqual([{ kind: "text", text: "I love fish!" }]);
  });
});
