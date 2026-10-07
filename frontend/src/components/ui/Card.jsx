export default function Card({ title, subtitle, children, className = "" }) {
  return (
    <div
      className={`rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors ${className}`}
    >
      {title && (
        <div className="border-b border-slate-100 dark:border-slate-800 px-5 py-3">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
