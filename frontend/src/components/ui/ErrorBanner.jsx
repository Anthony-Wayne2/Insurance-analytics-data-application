export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/40 px-4 py-3 text-sm text-rose-700 dark:text-rose-300 flex items-center justify-between">
      <span>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="ml-4 rounded-md border border-rose-300 dark:border-rose-800 bg-white dark:bg-slate-900 px-2.5 py-1 text-xs font-medium text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-950/60"
        >
          Retry
        </button>
      )}
    </div>
  );
}
