export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 flex items-center justify-between">
      <span>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="ml-4 rounded-md border border-rose-300 bg-white px-2.5 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100"
        >
          Retry
        </button>
      )}
    </div>
  );
}
