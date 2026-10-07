export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-sm text-slate-500 dark:text-slate-400">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 dark:border-slate-600 border-t-sky-500" />
      <span>{label}</span>
    </div>
  );
}
