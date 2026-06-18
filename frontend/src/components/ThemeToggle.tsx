"use client";

import { Moon, Sun, SunMoon } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";

function timeBasedTheme(): Theme {
  const h = new Date().getHours();
  return h >= 19 || h < 7 ? "dark" : "light";
}

function readTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const override = localStorage.getItem("aria-theme-override");
  if (override === "light" || override === "dark") return override;
  return timeBasedTheme();
}

export function ThemeToggle() {
  // The inline script in <head> already set data-theme on <html> before
  // first paint, but that value (e.g. "dark" in the evening) can differ from
  // this component's SSR-rendered default ("light"). Render a neutral icon
  // until mounted, then read the real theme - avoids a hydration mismatch.
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<Theme>("light");
  const [isOverridden, setIsOverridden] = useState(false);

  useEffect(() => {
    setTheme(readTheme());
    setIsOverridden(!!localStorage.getItem("aria-theme-override"));
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme, mounted]);

  // Re-evaluate the automatic theme as the clock crosses a boundary, as long
  // as the user hasn't manually overridden it for this session.
  useEffect(() => {
    if (isOverridden) return;
    const id = setInterval(() => {
      const next = timeBasedTheme();
      setTheme((prev) => (prev === next ? prev : next));
    }, 60_000);
    return () => clearInterval(id);
  }, [isOverridden]);

  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    localStorage.setItem("aria-theme-override", next);
    setIsOverridden(true);
    setTheme(next);
  };

  const resetToAuto = () => {
    localStorage.removeItem("aria-theme-override");
    setIsOverridden(false);
    setTheme(timeBasedTheme());
  };

  return (
    <div className="flex items-center gap-1.5">
      <button
        onClick={toggle}
        aria-label="Toggle theme"
        className="glass-card flex h-9 w-9 items-center justify-center rounded-full text-foreground transition hover:scale-105 active:scale-95"
      >
        {theme === "dark" ? <Moon size={16} /> : <Sun size={16} />}
      </button>
      {isOverridden && (
        <button
          onClick={resetToAuto}
          aria-label="Use time-of-day theme"
          title="Back to automatic, time-of-day theme"
          className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition hover:text-foreground"
        >
          <SunMoon size={16} />
        </button>
      )}
    </div>
  );
}
