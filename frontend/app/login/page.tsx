"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
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
    <main className="ds-page">
      <div className="ds-shell">
        <nav className="ds-nav">
          <Link href="/" className="ds-mark">
            DevStack
          </Link>
          <ThemeToggle />
        </nav>

        <section className="flex min-h-[calc(100vh-6rem)] items-center justify-center py-12">
          <div className="ds-card w-full max-w-md p-8">
            <p className="ds-eyebrow">Session</p>
            <h1 className="mt-3 text-3xl font-bold">Log in</h1>
            <p className="mt-2 text-sm text-[var(--ds-muted)]">Access your dashboard.</p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <label className="block">
                <span className="text-sm font-bold">Email</span>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="ds-field"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold">Password</span>
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

            <div className="mt-6 flex items-center justify-between text-sm">
              <Link href="/register" className="ds-link">
                Create account
              </Link>
              <Link href="/forgot-password" className="text-[var(--ds-muted)] hover:text-[var(--ds-accent)]">
                Forgot password?
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
