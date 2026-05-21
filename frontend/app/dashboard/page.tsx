"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

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
      <main className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-700">
        Loading...
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/dashboard" className="font-semibold text-slate-950">
            Dashboard
          </Link>
          <button
            type="button"
            onClick={() => signOut()}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-cyan-700">
            Signed in
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
            Welcome, {user.fullName ?? user.email}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            This is the starter dashboard. Replace these panels with your app workflow.
          </p>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Role</p>
            <p className="mt-2 text-xl font-semibold text-slate-950">{user.role}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Email</p>
            <p className="mt-2 truncate text-xl font-semibold text-slate-950">{user.email}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Verified</p>
            <p className="mt-2 text-xl font-semibold text-slate-950">
              {user.isVerified ? "Yes" : "No"}
            </p>
          </div>
        </div>

        {!user.isVerified ? (
          <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-medium text-amber-900">Email verification pending</p>
            <p className="mt-1 text-sm text-amber-800">
              In local development, the verification link is logged by the backend.
            </p>
            <button
              type="button"
              onClick={() => resendVerification()}
              className="mt-4 rounded-md bg-amber-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
            >
              Send verification email
            </button>
          </div>
        ) : null}
      </section>
    </main>
  );
}
