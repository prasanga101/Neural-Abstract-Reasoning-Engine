function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-white/65 px-2 py-1.5">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-800">{value}</p>
    </div>
  )
}

export function FinalStatePanel({ state }) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-1.5">
        <Metric label="Ambulances" value={state.ambulances} />
        <Metric label="Shelters" value={state.shelters} />
        <Metric label="Hospitals" value={state.hospitals.length} />
        <Metric label="Blocked" value={state.blocked_routes.length} />
      </div>
      <div className="rounded-xl border border-indigo-100/70 bg-white/70 px-2 py-1.5 text-[11px]">
        <p className="text-slate-500">Best route</p>
        <p className="font-semibold text-indigo-700">
          {state.best_route.distance} km - {state.best_route.duration} min
        </p>
      </div>
    </div>
  )
}
