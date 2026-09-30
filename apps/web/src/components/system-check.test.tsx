import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SessionState } from "@/lib/supabase/use-session";

import { SystemCheck } from "./system-check";

const mocks = vi.hoisted(() => ({
  GET: vi.fn(),
  session: { status: "signed-out" } as SessionState,
}));

vi.mock("@/lib/api/client", () => ({ api: { GET: mocks.GET } }));
vi.mock("@/lib/supabase/use-session", () => ({ useSession: () => mocks.session }));

function renderCheck() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <SystemCheck />
    </QueryClientProvider>,
  );
}

function row(label: string) {
  return screen.getByText(label).closest("li")!;
}

describe("SystemCheck", () => {
  beforeEach(() => {
    mocks.GET.mockReset();
  });

  it("reports the API as reachable and skips the auth checks when signed out", async () => {
    mocks.session = { status: "signed-out" };
    mocks.GET.mockResolvedValue({ data: { status: "ok" }, response: { status: 200 } });

    renderCheck();

    expect(await within(row("API reachable")).findByText("(ok)")).toBeTruthy();
    expect(within(row("Protected API route")).getByText("(skipped)")).toBeTruthy();
    expect(mocks.GET).toHaveBeenCalledWith("/api/v1/health");
    expect(mocks.GET).not.toHaveBeenCalledWith("/api/v1/me");
  });

  it("calls the protected route once signed in", async () => {
    mocks.session = { status: "signed-in", userId: "u-1", email: "astrid@berk.test" };
    mocks.GET.mockImplementation(async (path: string) =>
      path === "/api/v1/me"
        ? { data: { id: "u-1", role: "authenticated" }, response: { status: 200 } }
        : { data: { status: "ok" }, response: { status: 200 } },
    );

    renderCheck();

    expect(await within(row("Protected API route")).findByText("(ok)")).toBeTruthy();
    expect(screen.getByText("GET /api/v1/me → u-1")).toBeTruthy();
  });

  it("shows the HTTP status when the protected route rejects the token", async () => {
    mocks.session = { status: "signed-in", userId: "u-1", email: undefined };
    mocks.GET.mockImplementation(async (path: string) =>
      path === "/api/v1/me"
        ? { error: { detail: "Invalid or expired token" }, response: { status: 401 } }
        : { data: { status: "ok" }, response: { status: 200 } },
    );

    renderCheck();

    expect(await within(row("Protected API route")).findByText("(error)")).toBeTruthy();
    expect(screen.getByText("HTTP 401")).toBeTruthy();
  });
});
