"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading, signOut, resendVerification } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login?returnTo=/dashboard");
    }
  }, [isLoading, router, user]);

  if (isLoading || !user) {
    return (
      <main className="ds-page flex items-center justify-center">
        <p className="ds-eyebrow">Loading session</p>
      </main>
    );
  }

  return (
    <main className="ds-page">
      <div className="ds-shell">
        <header className="ds-nav">
          <Link href="/dashboard" className="ds-mark">
            Dashboard
          </Link>
          <div className="ds-nav-actions">
            <Link href="/admin" className="ds-pill ds-pill-outline">
              Admin
            </Link>
            <button type="button" onClick={() => signOut()} className="ds-pill ds-pill-outline">
              Sign out
            </button>
            <ThemeToggle />
          </div>
        </header>

        <section className="py-10">
          <div>
            <p className="ds-eyebrow">Signed in</p>
            <h1 className="mt-3 text-4xl font-bold leading-tight sm:text-5xl">
              Welcome, {user.fullName ?? user.email}
            </h1>
            <p className="ds-muted mt-3 max-w-2xl text-sm">
              This is the starter dashboard. Replace these panels with your app workflow.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="ds-stat">
              <p className="ds-eyebrow">Role</p>
              <p className="text-2xl font-black">{user.role}</p>
            </div>
            <div className="ds-stat">
              <p className="ds-eyebrow">Email</p>
              <p className="truncate text-2xl font-black">{user.email}</p>
            </div>
            <div className="ds-stat">
              <p className="ds-eyebrow">Verified</p>
              <p className="text-2xl font-black">{user.isVerified ? "Yes" : "No"}</p>
            </div>
          </div>

          {!user.isVerified ? (
            <div className="ds-panel mt-6 p-5">
              <p className="text-sm font-bold">Email verification pending</p>
              <p className="ds-muted mt-1 text-sm">
                In local development, the verification link is logged by the backend.
              </p>
              <button
                type="button"
                onClick={() => resendVerification()}
                className="ds-pill ds-pill-primary mt-4"
              >
                Send verification email
              </button>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
