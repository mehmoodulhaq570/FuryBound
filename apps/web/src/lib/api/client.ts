import createFetchClient, { type Middleware } from "openapi-fetch";

import { env } from "@/lib/env";
import { createClient as createSupabaseClient } from "@/lib/supabase/client";

import type { paths } from "./schema";

const attachSupabaseToken: Middleware = {
  async onRequest({ request }) {
    const { data } = await createSupabaseClient().auth.getSession();
    const token = data.session?.access_token;
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
};

/** Typed client for the FastAPI backend. Types come from `pnpm gen:api-types`. */
export const api = createFetchClient<paths>({ baseUrl: env.apiUrl });
api.use(attachSupabaseToken);
