"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { LocalEmailHint } from "@/components/local-email-hint";
import { useAuth } from "@/lib/auth";

export default function VerifyEmailPage() {
  const { verifyEmail } = useAuth();
  const [message, setMessage] = useState("Verifying your email...");
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) {
      window.setTimeout(() => {
        if (!active) return;
        setMessage("Verification token is missing.");
        setIsError(true);
      }, 0);
      return;
    }
    verifyEmail(token).then((result) => {
      if (!active) return;
      if (result.error) {
        setMessage(result.error.message);
        setIsError(true);
        return;
      }
      setMessage(result.message);
      setIsError(false);
    });
    return () => {
      active = false;
    };
  }, [verifyEmail]);

  return (
    <AuthShell
      kicker="Verification"
      title="Email verification"
      subtitle="Use the local verification link to mark your account as verified."
    >
      <LocalEmailHint action="verification" />

      <p className={`mt-6 text-sm font-bold ${isError ? "text-[var(--ds-danger)]" : "text-[var(--ds-success)]"}`}>
        {message}
      </p>
      <div className="ds-auth-actions">
        <Link href="/dashboard" className="ds-pill ds-pill-primary">
          Open dashboard
        </Link>
        <Link href="/login" className="ds-auth-link ds-auth-link-muted">
          Back to login
        </Link>
      </div>
    </AuthShell>
  );
}
