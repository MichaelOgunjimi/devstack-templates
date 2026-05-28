"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsPending(true);
    const result = await signUp({ email, password, fullName });
    setIsPending(false);
    if (result.error) {
      setError(result.error.message);
      return;
    }
    router.replace("/dashboard");
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
            <p className="ds-eyebrow">Identity</p>
            <h1 className="mt-3 text-3xl font-bold">Create account</h1>
            <p className="mt-2 text-sm text-[var(--ds-muted)]">Start with a user account.</p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <label className="block">
                <span className="text-sm font-bold">Full name</span>
                <input
                  type="text"
                  required
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  className="ds-field"
                />
              </label>

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
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="ds-field"
                />
              </label>

              {error ? <p className="text-sm font-bold ds-error">{error}</p> : null}

              <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
                {isPending ? "Creating..." : "Create account"}
              </button>
            </form>

            <p className="mt-6 text-sm text-[var(--ds-muted)]">
              Already have an account?{" "}
              <Link href="/login" className="ds-link">
                Log in
              </Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
