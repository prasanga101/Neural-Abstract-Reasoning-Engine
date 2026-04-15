const statusColor = {
  completed: 'bg-emerald-500',
  skipped: 'bg-amber-400',
  failed: 'bg-rose-500',
}

export function ExecutorPanel({ executor }) {
  return (
    <div className="space-y-2.5">
      <div className="text-[11px] text-slate-500">
        Execution status: {' '}
        <span className="font-semibold capitalize text-slate-800">
          {executor.status}
        </span>
      </div>
      <ol className="space-y-1">
        {executor.timeline.slice(0, 5).map((item) => (
          <li
            key={`${item.step}-${item.node}`}
            className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-white/65 px-2.5 py-1.5 text-[11px]"
          >
            <div>
              <span className="mr-1 text-slate-400">#{item.step}</span>
              <span className="text-slate-600">{item.node}</span>
            </div>
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${statusColor[item.status] || 'bg-slate-400'}`}
              title={item.status}
            />
          </li>
        ))}
      </ol>
    </div>
  )
}
