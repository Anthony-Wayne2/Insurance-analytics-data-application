export default function Card({
  title,
  subtitle,
  children,
  className = "",
  padded = true,
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}
    >
      {title && (
        <div className={`border-b border-slate-100 ${padded ? "px-5 py-3" : "px-5 py-3"}`}>
          <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
          )}
        </div>
      )}
      <div className={padded ? "p-5" : ""}>{children}</div>
    </div>
  );
}
