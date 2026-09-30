import { createBrowserClient } from "@supabase/ssr";

import { env } from "@/lib/env";

/** Browser Supabase client. `createBrowserClient` returns a singleton in the browser. */
export function createClient() {
  return createBrowserClient(env.supabaseUrl, env.supabasePublishableKey);
}
