import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in · Dragon Academy" };

export default function LoginPage() {
  return (
    <div className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
      {/* The form reads ?next= from the URL, which needs a Suspense boundary. */}
      <Suspense>
        <LoginForm />
      </Suspense>
    </div>
  );
}
