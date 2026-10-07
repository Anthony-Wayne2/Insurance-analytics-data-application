import { useTheme } from "../../context/ThemeContext";

export default function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Insurance Analytics
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Claims, providers, and payments at a glance
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 dark:text-slate-500">
            Prototype · v0.1
          </span>
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 px-2.5 py-1 text-sm transition-colors"
          >
            {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
          </button>
        </div>
      </div>
    </header>
  );
}
