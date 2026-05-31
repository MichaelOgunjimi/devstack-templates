"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth";

function safeReturnTo(value: string | null): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsPending(true);
    const result = await signIn({ email, password });
    setIsPending(false);
    if (result.error) {
      setError(result.error.message);
      return;
    }
    const params = new URLSearchParams(window.location.search);
    router.replace(safeReturnTo(params.get("returnTo")));
  }

  return (
    <AuthShell kicker="Session" title="Log in" subtitle="Access your dashboard.">
      <form onSubmit={handleSubmit} className="ds-auth-form">
        <label className="ds-auth-field">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="ds-field"
          />
        </label>

        <label className="ds-auth-field">
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="ds-field"
          />
        </label>

        {error ? <p className="text-sm font-bold ds-error">{error}</p> : null}

        <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
          {isPending ? "Logging in..." : "Log in"}
        </button>
      </form>

      <div className="ds-auth-actions">
        <p className="ds-auth-prompt">
          New here?{" "}
          <Link href="/register" className="ds-auth-link">
            Create account
          </Link>
        </p>
        <Link href="/forgot-password" className="ds-auth-link ds-auth-link-muted">
          Forgot password?
        </Link>
      </div>
    </AuthShell>
  );
}
