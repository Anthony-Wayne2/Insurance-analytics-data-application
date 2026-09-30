export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            Insurance Analytics
          </h1>
          <p className="text-xs text-slate-500">
            Claims, providers, and payments at a glance
          </p>
        </div>
        <span className="text-xs text-slate-400">Prototype · v0.1</span>
      </div>
    </header>
  );
}
