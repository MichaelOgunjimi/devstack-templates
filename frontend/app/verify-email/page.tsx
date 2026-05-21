"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
      setMessage("Verification token is missing.");
      setIsError(true);
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
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6 py-12">
      <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Email verification</h1>
        <p className={`mt-4 text-sm font-medium ${isError ? "text-red-600" : "text-emerald-700"}`}>
          {message}
        </p>
        <Link
          href="/dashboard"
          className="mt-8 inline-flex rounded-md bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Open dashboard
        </Link>
      </section>
    </main>
  );
}
