"use client";

import { useEffect } from "react";

function applyTheme(theme: "light" | "dark") {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export function ThemeToggle() {
  useEffect(() => {
    const stored = window.localStorage.getItem("theme");
    const theme = stored === "light" || stored === "dark" ? stored : "light";
    applyTheme(theme);
  }, []);

  function toggleTheme() {
    const nextTheme = document.documentElement.classList.contains("dark") ? "light" : "dark";
    window.localStorage.setItem("theme", nextTheme);
    applyTheme(nextTheme);
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="ds-icon-button"
      aria-label="Toggle color mode"
      title="Toggle color mode"
    >
      <svg aria-hidden className="theme-icon theme-sun" viewBox="0 0 24 24">
        <path d="M12 4V2m0 20v-2m8-8h2M2 12h2m13.66-5.66 1.42-1.42M4.92 19.08l1.42-1.42m0-11.32L4.92 4.92m14.16 14.16-1.42-1.42" />
        <circle cx="12" cy="12" r="4" />
      </svg>
      <svg aria-hidden className="theme-icon theme-moon" viewBox="0 0 24 24">
        <path d="M20.4 14.6A8 8 0 0 1 9.4 3.6 8.5 8.5 0 1 0 20.4 14.6Z" />
      </svg>
    </button>
  );
}
