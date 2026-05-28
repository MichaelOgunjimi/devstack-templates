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
      className="ds-pill ds-pill-outline min-w-11 px-3"
      aria-label="Toggle color mode"
      title="Toggle color mode"
    >
      <span aria-hidden className="theme-sun">
        Light
      </span>
      <span aria-hidden className="theme-moon">
        Dark
      </span>
    </button>
  );
}
