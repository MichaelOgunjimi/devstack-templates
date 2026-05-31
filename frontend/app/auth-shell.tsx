"use client";

import type { ReactNode } from "react";

import { ThemeToggle } from "@/components/theme-toggle";

export function AuthShell({
  kicker,
  title,
  subtitle,
  children,
}: {
  kicker: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <main className="ds-page ds-auth-page">
      <div className="ds-atmosphere" />
      <ThemeToggle />
      <section className="ds-auth-shell">
        <aside className="ds-auth-context" aria-hidden="true">
          <div className="ds-auth-context-top">
            <span>DevStack Access</span>
            <span>Auth</span>
          </div>
          <div className="ds-auth-context-body">
            <p className="ds-card-kicker">Starter layer</p>
            <h2>User sessions, local email, and admin routes.</h2>
            <div className="ds-auth-signals">
              <span>JWT</span>
              <span>Verify</span>
              <span>Reset</span>
            </div>
          </div>
        </aside>
        <section className="ds-auth-panel">
          <p className="ds-label">{kicker}</p>
          <h1>{title}</h1>
          <p className="ds-auth-subtitle">{subtitle}</p>
          {children}
        </section>
      </section>
    </main>
  );
}
