"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth";

export default function AdminPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login?returnTo=/admin");
    }
  }, [isLoading, router, user]);

  if (isLoading || !user) {
    return (
      <main className="ds-page flex items-center justify-center">
        <p className="ds-eyebrow">Loading session</p>
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className="ds-page flex items-center justify-center px-6">
        <section className="ds-card w-full max-w-md p-8 text-center">
          <p className="ds-eyebrow">Restricted</p>
          <h1 className="mt-3 text-3xl font-bold">Access denied</h1>
          <p className="mt-3 text-sm opacity-75">This page requires the admin role.</p>
          <Link href="/dashboard" className="ds-pill ds-pill-primary mt-8">
            Back to dashboard
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="ds-page">
      <div className="ds-shell">
        <header className="ds-nav">
          <Link href="/admin" className="ds-mark">
            Admin
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="ds-pill ds-pill-outline">
              Dashboard
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <section className="py-10">
          <div className="ds-card p-6">
            <p className="ds-eyebrow">Admin area</p>
            <h1 className="mt-3 text-4xl font-bold leading-tight">Starter admin dashboard</h1>
            <p className="mt-3 text-sm opacity-75">
              Add user management, moderation, billing, or internal tools here.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
