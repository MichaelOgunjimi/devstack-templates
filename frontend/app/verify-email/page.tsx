"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
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
    <main className="ds-page">
      <div className="ds-shell">
        <nav className="ds-nav">
          <Link href="/" className="ds-mark">
            DevStack
          </Link>
          <ThemeToggle />
        </nav>

        <section className="flex min-h-[calc(100vh-6rem)] items-center justify-center py-12">
          <div className="ds-card w-full max-w-md p-8 text-center">
            <p className="ds-eyebrow">Verification</p>
            <h1 className="mt-3 text-3xl font-bold">Email verification</h1>
            <p className={`mt-4 text-sm font-bold ${isError ? "text-red-500" : "text-emerald-500"}`}>
              {message}
            </p>
            <Link href="/dashboard" className="ds-pill ds-pill-primary mt-8">
              Open dashboard
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
