export function RouterPanel({ router }) {
  return (
    <div className="space-y-2.5">
      <div className="rounded-xl border border-blue-100/70 bg-white/70 px-2.5 py-1.5 text-[11px] text-slate-600">
        Routed top intent <span className="font-semibold text-blue-700">{router.top}</span>
      </div>
      {router.rl?.action ? (
        <div className="rounded-xl border border-cyan-100/80 bg-cyan-50/70 px-2.5 py-2 text-[11px] text-slate-700">
          <div>
            RL action <span className="font-semibold text-cyan-800">{router.rl.action}</span>
          </div>
          <div className="mt-1 text-slate-500">
            source: {router.rl.source ?? 'unknown'}
            {router.rl.injected ? ' · injected into final tasks' : ' · already matched final tasks'}
          </div>
        </div>
      ) : null}
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
