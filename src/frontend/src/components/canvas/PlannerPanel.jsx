export function PlannerPanel({ planner }) {
  return (
    <div className="space-y-2.5">
      <div className="rounded-xl border border-emerald-100/70 bg-white/70 px-2.5 py-1.5 text-[11px] text-emerald-700">
        Planning focus <span className="font-semibold">{planner.top}</span>
      </div>
      {planner.scores.slice(0, 4).map((item) => (
        <div key={item.node} className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-600">{item.node}</span>
            <span className="font-medium text-slate-800">
              {(item.score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100">
            <div
              className="h-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
              style={{ width: `${item.score * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
