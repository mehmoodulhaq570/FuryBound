import { SystemCheck } from "@/components/system-check";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <p className="text-accent text-sm font-medium tracking-widest uppercase">Phase 0</p>
        <h1 className="text-4xl font-semibold tracking-tight">Dragon Academy</h1>
        <p className="text-muted max-w-prose">
          The dragon chooses you. Take the quiz, meet your dragon, train it, talk to it and go on
          adventures together. Nothing is playable yet: this page checks that the web app, API and
          auth are wired together.
        </p>
      </section>
      <SystemCheck />
    </div>
  );
}
