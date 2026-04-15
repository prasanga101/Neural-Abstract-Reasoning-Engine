function tokenizeMessage(message) {
  return message
    .split(/[,.]/)
    .map((token) => token.trim())
    .filter(Boolean)
}

export function EmergencyContextPanel({ message }) {
  const chunks = tokenizeMessage(message)

  return (
    <div className="space-y-2.5">
      <p className="text-[11px] text-slate-500">
        Context encoding stream
      </p>
      <div className="space-y-1.5">
        {chunks.map((chunk, index) => (
          <div
            key={`${chunk}-${index}`}
            className="group relative overflow-hidden rounded-xl border border-cyan-100/80 bg-white/75 px-2.5 py-1.5 text-[11px] text-slate-700"
          >
            <span className="absolute inset-y-0 left-0 w-1 rounded-l-xl bg-gradient-to-b from-cyan-300/80 to-blue-300/80" />
            <div className="pl-2">
              <span className="mr-2 font-semibold uppercase tracking-[0.08em] text-cyan-600/90">
                c{index + 1}
              </span>
              <span className="text-slate-600">{chunk}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
