"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth";

export default function ResetPasswordPage() {
  const router = useRouter();
  const { resetPassword } = useAuth();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) {
      setError("Reset token is missing.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsPending(true);
    const result = await resetPassword(token, password);
    setIsPending(false);
    if (result.error) {
      setError(result.error.message);
      return;
    }
    setMessage(result.message);
    window.setTimeout(() => router.replace("/login"), 1600);
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
            <p className="ds-eyebrow">Credentials</p>
            <h1 className="mt-3 text-3xl font-bold">Set new password</h1>
            <p className="mt-2 text-sm opacity-75">Choose a new password for your account.</p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <label className="block">
                <span className="text-sm font-bold">New password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="ds-field"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold">Confirm password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className="ds-field"
                />
              </label>

              {message ? <p className="text-sm font-bold text-emerald-500">{message}</p> : null}
              {error ? <p className="text-sm font-bold text-red-500">{error}</p> : null}

              <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
                {isPending ? "Saving..." : "Reset password"}
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
