/** A generic dragon in flight, seen from below. Decorative: not any particular species. */
export function Silhouette({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 64" aria-hidden="true" className={className} fill="currentColor">
      <path d="M48 26C40 10 22 4 2 8c10 6 16 12 20 20 6-2 14 0 20 6 2-4 4-6 6-8Z" />
      <path d="M52 26c8-16 26-22 46-18-10 6-16 12-20 20-6-2-14 0-20 6-2-4-4-6-6-8Z" />
      <ellipse cx="50" cy="34" rx="6" ry="16" />
      <circle cx="50" cy="15" r="5" />
      <path d="M48 48c0 6 2 10 8 14-6-1-10-5-11-12Z" />
    </svg>
  );
}
