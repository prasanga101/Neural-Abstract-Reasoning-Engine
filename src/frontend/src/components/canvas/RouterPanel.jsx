export function RouterPanel({ router }) {
  return (
    <div className="space-y-2.5">
      <div className="rounded-xl border border-blue-100/70 bg-white/70 px-2.5 py-1.5 text-[11px] text-slate-600">
        Routed top intent <span className="font-semibold text-blue-700">{router.top}</span>
      </div>
      {router.scores.slice(0, 3).map((item) => (
        <div key={item.task} className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-600">{item.task}</span>
            <span className="font-medium text-slate-800">
              {(item.score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100">
            <div
              className="h-1.5 rounded-full bg-gradient-to-r from-blue-400 to-blue-600"
              style={{ width: `${item.score * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
