"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth";

export default function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setIsPending(true);
    const result = await forgotPassword(email);
    setIsPending(false);
    if (result.error) {
      setError(result.error.message);
      return;
    }
    setMessage(result.message);
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
            <p className="ds-eyebrow">Recovery</p>
            <h1 className="mt-3 text-3xl font-bold">Reset password</h1>
            <p className="mt-2 text-sm text-[var(--ds-muted)]">
              Enter your email and check the backend logs for the local reset link.
            </p>

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

              {message ? <p className="text-sm font-bold ds-success">{message}</p> : null}
              {error ? <p className="text-sm font-bold ds-error">{error}</p> : null}

              <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
                {isPending ? "Sending..." : "Send reset link"}
              </button>
            </form>

            <Link href="/login" className="ds-link mt-6 inline-block text-sm">
              Back to login
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
