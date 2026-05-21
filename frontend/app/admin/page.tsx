"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

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
      <main className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-700">
        Loading...
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
        <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Access denied</h1>
          <p className="mt-3 text-sm text-slate-600">This page requires the admin role.</p>
          <Link
            href="/dashboard"
            className="mt-8 inline-flex rounded-md bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Back to dashboard
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/admin" className="font-semibold text-slate-950">
            Admin
          </Link>
          <Link href="/dashboard" className="text-sm font-medium text-cyan-700 hover:text-cyan-800">
            Dashboard
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-cyan-700">
            Admin area
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
            Starter admin dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Add user management, moderation, billing, or internal tools here.
          </p>
        </div>
      </section>
    </main>
  );
}
