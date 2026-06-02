"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { LocalEmailHint } from "@/components/local-email-hint";
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
    <AuthShell
      kicker="Recovery"
      title="Reset password"
      subtitle="Enter your email and use the local reset link to choose a new password."
    >
      <LocalEmailHint action="password reset" />

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

        {message ? <p className="text-sm font-bold ds-success">{message}</p> : null}
        {error ? <p className="text-sm font-bold ds-error">{error}</p> : null}

        <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
          {isPending ? "Sending..." : "Send reset link"}
        </button>
      </form>

      <div className="ds-auth-actions">
        <p className="ds-auth-prompt">
          Remembered it?{" "}
          <Link href="/login" className="ds-auth-link">
            Back to login
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
