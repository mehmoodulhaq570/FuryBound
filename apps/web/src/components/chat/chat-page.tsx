"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { DragonPortrait } from "@/components/art/dragon-portrait";
import { DragonGate } from "@/components/training/dragon-gate";
import { api } from "@/lib/api/client";
import { replyParts, sseReader, type ChatMessage } from "@/lib/chat/parse";
import { myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";

type Mode = "narrated" | "talking";
const MAX_CHARS = 500;
const MODE_KEY = "dragon-academy:chat-mode";

const messagesKey = (dragonId: string) => ["chat", dragonId] as const;

function readMode(): Mode {
  try {
    return localStorage.getItem(MODE_KEY) === "talking" ? "talking" : "narrated";
  } catch {
    return "narrated";
  }
}

/** A dragon's reply: actions in italics, thoughts in a bubble, anything else as text. */
export function DragonReply({ text }: { text: string }) {
  return (
    <div className="space-y-1">
      {replyParts(text).map((part, i) =>
        part.kind === "action" ? (
          <p key={i} className="text-muted italic">
            {part.text}
          </p>
        ) : part.kind === "thought" ? (
          <p key={i} className="bg-accent/10 inline-block rounded-2xl rounded-tl-sm px-3 py-1.5">
            <span aria-label="thinks">💭</span> {part.text}
          </p>
        ) : (
          <p key={i}>{part.text}</p>
        ),
      )}
    </div>
  );
}

function Bubble({ message, dragon }: { message: ChatMessage; dragon: PlayerDragon }) {
  if (message.role === "user") {
    return (
      <li className="flex justify-end">
        <p className="bg-accent max-w-[80%] rounded-2xl rounded-br-sm px-4 py-2 text-white">
          {message.content}
        </p>
      </li>
    );
  }
  return (
    <li className="flex items-start gap-3">
      <DragonPortrait
        speciesId={dragon.species_id}
        speciesName={dragon.species_name}
        sizes="40px"
        className="size-10 shrink-0"
      />
      <div className="bg-surface border-line max-w-[80%] rounded-2xl rounded-tl-sm border px-4 py-2">
        <DragonReply text={message.content} />
      </div>
    </li>
  );
}

function Chat({ dragon, userId }: { dragon: PlayerDragon; userId: string }) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>(readMode);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  const history = useQuery({
    queryKey: messagesKey(dragon.id),
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/dragons/{dragon_id}/messages", {
        params: { path: { dragon_id: dragon.id } },
      });
      if (error || !data) throw new Error(`HTTP ${response.status}`);
      return data;
    },
  });

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [history.data, streaming]);

  function chooseMode(next: Mode) {
    setMode(next);
    try {
      localStorage.setItem(MODE_KEY, next);
    } catch {
      // Not fatal: the choice just isn't remembered.
    }
  }

  async function send() {
    const text = draft.trim();
    if (!text || streaming !== null) return;
    const add = (m: ChatMessage) =>
      queryClient.setQueryData<ChatMessage[]>(messagesKey(dragon.id), (old) => [...(old ?? []), m]);

    setError(null);
    setDraft("");
    // Show the player's message at once; the saved copy comes with the next history load.
    add({
      id: -Date.now(),
      role: "user",
      content: text,
      mode,
      created_at: new Date().toISOString(),
    });
    setStreaming("");

    const { data, error, response } = await api.POST("/api/v1/dragons/{dragon_id}/chat", {
      params: { path: { dragon_id: dragon.id } },
      body: { message: text, mode },
      parseAs: "stream",
    });
    if (error || !data) {
      setStreaming(null);
      setError(error?.detail?.toString() ?? `Something went wrong (HTTP ${response.status})`);
      return;
    }

    let reply = "";
    const read = sseReader((event) => {
      if (event.type === "delta") {
        reply += event.text;
        setStreaming(reply);
      } else {
        add(event.message);
      }
    });
    const reader = data.pipeThrough(new TextDecoderStream()).getReader();
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        read(value);
      }
    } catch {
      setError("The connection dropped. Try again.");
    }
    setStreaming(null);
    // Chatting is logged, so the dragon's mood and memory may have changed.
    queryClient.invalidateQueries({ queryKey: myDragonQueryKey(userId) });
  }

  const messages = history.data ?? [];
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <DragonPortrait
            speciesId={dragon.species_id}
            speciesName={dragon.species_name}
            sizes="56px"
            className="size-14"
          />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{dragon.name}</h1>
            <p className="text-muted text-sm">
              {dragon.mood.label} ·{" "}
              <Link href="/dragon" className="underline">
                look after {dragon.name}
              </Link>
            </p>
          </div>
        </div>
        <fieldset className="border-line flex rounded-lg border p-1 text-sm">
          <legend className="sr-only">How your dragon replies</legend>
          {(["narrated", "talking"] as const).map((m) => (
            <label
              key={m}
              className={`cursor-pointer rounded-md px-3 py-1 ${mode === m ? "bg-accent text-white" : ""}`}
            >
              <input
                type="radio"
                name="mode"
                value={m}
                checked={mode === m}
                onChange={() => chooseMode(m)}
                className="sr-only"
              />
              {m === "narrated" ? "Narrated" : "Talking (just for fun)"}
            </label>
          ))}
        </fieldset>
      </header>
      <p className="text-muted text-xs">
        {mode === "narrated"
          ? "Dragons don't speak our language: you'll see what it does, and what it thinks."
          : "Talking mode isn't how dragons work in the films, but it's fun."}{" "}
        Replies are written by an AI and can be wrong or odd.
      </p>

      <ul className="space-y-4" aria-live="polite">
        {history.isPending && <li className="text-muted">Loading…</li>}
        {messages.length === 0 && !history.isPending && (
          <li className="text-muted text-center text-sm">Say hello to {dragon.name}.</li>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} message={m} dragon={dragon} />
        ))}
        {streaming !== null && (
          <li className="flex items-start gap-3">
            <DragonPortrait
              speciesId={dragon.species_id}
              speciesName={dragon.species_name}
              sizes="40px"
              className="size-10 shrink-0"
            />
            <div className="bg-surface border-line max-w-[80%] rounded-2xl rounded-tl-sm border px-4 py-2">
              {streaming ? <DragonReply text={streaming} /> : <span className="text-muted">…</span>}
            </div>
          </li>
        )}
      </ul>
      <div ref={bottom} />

      {error && (
        <p role="alert" className="text-bad text-sm">
          {error}
        </p>
      )}
      <form
        className="bg-background sticky bottom-0 flex gap-2 py-3"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <label className="sr-only" htmlFor="chat-input">
          Message to {dragon.name}
        </label>
        <input
          id="chat-input"
          value={draft}
          maxLength={MAX_CHARS}
          autoComplete="off"
          placeholder={`Say something to ${dragon.name}…`}
          onChange={(e) => setDraft(e.target.value)}
          className="bg-surface border-line focus-visible:outline-accent min-w-0 flex-1 rounded-lg border px-3 py-2"
        />
        <button
          type="submit"
          disabled={!draft.trim() || streaming !== null}
          className="bg-accent rounded-lg px-4 py-2 font-medium text-white disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  );
}

export function ChatPage() {
  return (
    <DragonGate title="Talk to your dragon" path="/chat">
      {(dragon, userId) => <Chat dragon={dragon} userId={userId} />}
    </DragonGate>
  );
}
