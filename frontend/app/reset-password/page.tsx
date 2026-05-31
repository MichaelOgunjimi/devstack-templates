"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthShell } from "@/components/auth-shell";
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
    <AuthShell
      kicker="Credentials"
      title="Set new password"
      subtitle="Choose a new password for your account."
    >
      <form onSubmit={handleSubmit} className="ds-auth-form">
        <label className="ds-auth-field">
          New password
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

        <label className="ds-auth-field">
          Confirm password
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

        {message ? <p className="text-sm font-bold ds-success">{message}</p> : null}
        {error ? <p className="text-sm font-bold ds-error">{error}</p> : null}

        <button type="submit" disabled={isPending} className="ds-pill ds-pill-primary w-full">
          {isPending ? "Saving..." : "Reset password"}
        </button>
      </form>

      <div className="ds-auth-actions">
        <Link href="/login" className="ds-auth-link">
          Back to login
        </Link>
      </div>
    </AuthShell>
  );
}
