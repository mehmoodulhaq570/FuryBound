"use client";

import { useMemo, useState } from "react";

import { type Academy, isDiscovered, isNew, progress } from "@/lib/dragon-book/academy";
import {
  classesOf,
  createSearch,
  DEFAULT_FILTERS,
  type Filters,
  visibleCards,
} from "@/lib/dragon-book/filter";
import { APPEARANCE_LABELS, APPEARANCE_TYPES, filmLabel } from "@/lib/dragon-book/labels";
import type { AppearanceType, DragonCard as Card, Movie } from "@/lib/dragon-book/types";

import { DragonCard, LockedCard } from "./dragon-card";

const selectClass =
  "border-line bg-surface rounded-lg border px-3 py-2 text-sm focus-visible:outline-accent focus-visible:outline-2";

function Select<T extends string>({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  value: T | null;
  onChange: (value: T | null) => void;
  options: { value: T; label: string }[];
  disabled?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="text-muted">{label}</span>
      <select
        className={selectClass}
        value={value ?? ""}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value === "" ? null : (e.target.value as T))}
      >
        <option value="">Any</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/**
 * The Dragon Book list. With `academy` (a signed-in player), dragons they haven't met show
 * as "???" unless they choose "Show all".
 */
export function DragonBook({
  cards,
  movies,
  academy = null,
}: {
  cards: Card[];
  movies: Movie[];
  academy?: Academy | null;
}) {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [showAll, setShowAll] = useState(false);
  const search = useMemo(() => createSearch(cards), [cards]);
  const classes = useMemo(() => classesOf(cards), [cards]);
  const locking = academy !== null && !showAll;
  const locked = (card: Card) => locking && !isDiscovered(card, academy!);
  // Searching by name mustn't reveal which "???" is which.
  const shown = visibleCards(cards, filters, search).filter(
    (card) => !(filters.query.trim() && locked(card)),
  );
  const filtered = JSON.stringify(filters) !== JSON.stringify(DEFAULT_FILTERS);

  const set = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    setFilters((current) => ({ ...current, [key]: value }));

  return (
    <div className="space-y-6">
      {academy && (
        <AcademyBar academy={academy} cards={cards} showAll={showAll} onShowAll={setShowAll} />
      )}
      <div className="space-y-4">
        <label className="block">
          <span className="sr-only">Search dragons</span>
          <input
            type="search"
            placeholder="Search by name, e.g. Nadder"
            value={filters.query}
            onChange={(e) => set("query", e.target.value)}
            className={`${selectClass} w-full text-base`}
          />
        </label>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Select
            label="Film"
            value={filters.movie}
            onChange={(v) => set("movie", v)}
            options={movies.map((m) => ({ value: m.movie_id, label: filmLabel(m) }))}
          />
          <Select
            label="Kind"
            value={filters.kind === "all" ? null : filters.kind}
            onChange={(v) => set("kind", v ?? "all")}
            options={[
              { value: "species" as const, label: "Species" },
              { value: "individual" as const, label: "Named dragons" },
            ]}
          />
          <Select<AppearanceType>
            label="Appears as"
            value={filters.appearanceType}
            onChange={(v) => set("appearanceType", v)}
            options={APPEARANCE_TYPES.map((t) => ({ value: t, label: APPEARANCE_LABELS[t] }))}
          />
          <Select
            label="Class (franchise)"
            value={filters.includeFranchise ? filters.dragonClass : null}
            onChange={(v) => set("dragonClass", v)}
            options={classes.map((c) => ({ value: c, label: c }))}
            disabled={!filters.includeFranchise}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.includeFranchise}
              onChange={(e) => set("includeFranchise", e.target.checked)}
              className="accent-accent size-4"
            />
            Show franchise facts
            <span className="text-muted">(from outside the films)</span>
          </label>
          <p className="text-muted" aria-live="polite">
            Showing {shown.length} of {cards.length}
            {filtered && (
              <button
                type="button"
                onClick={() => setFilters(DEFAULT_FILTERS)}
                className="text-accent ml-3 underline-offset-2 hover:underline"
              >
                Clear filters
              </button>
            )}
          </p>
        </div>
      </div>

      {shown.length > 0 ? (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map((card) => (
            <li key={card.id}>
              {locked(card) ? (
                <LockedCard card={card} />
              ) : (
                <DragonCard
                  card={card}
                  movies={movies}
                  showClass={filters.includeFranchise}
                  isNew={academy !== null && isNew(card, academy)}
                />
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="border-line text-muted rounded-xl border border-dashed p-8 text-center">
          No dragons match. Try fewer filters or a different spelling.
        </p>
      )}
    </div>
  );
}

function AcademyBar({
  academy,
  cards,
  showAll,
  onShowAll,
}: {
  academy: Academy;
  cards: Card[];
  showAll: boolean;
  onShowAll: (showAll: boolean) => void;
}) {
  const { found, total } = progress(cards, academy);
  return (
    <div className="bg-surface border-line flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4">
      <div className="min-w-48 flex-1 space-y-2">
        <p className="text-sm">
          <span className="font-semibold">
            {found} / {total}
          </span>{" "}
          species discovered
        </p>
        <div
          role="progressbar"
          aria-label="Species discovered"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={found}
          className="bg-line h-2 overflow-hidden rounded-full"
        >
          <div
            className="bg-accent h-full rounded-full"
            style={{ width: `${total ? (found / total) * 100 : 0}%` }}
          />
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={showAll}
          onChange={(e) => onShowAll(e.target.checked)}
          className="accent-accent size-4"
        />
        Show all
      </label>
    </div>
  );
}
