function Pill({ label, value }) {
  return (
    <div className="rounded-full border border-slate-200/80 bg-white/65 px-2 py-1 text-[10px]">
      <span className="text-slate-500">{label}: </span>
      <span className={value ? 'text-emerald-600' : 'text-rose-600'}>
        {value ? 'pass' : 'fail'}
      </span>
    </div>
  )
}

export function VerifierPanel({ verifier }) {
  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap gap-1.5">
        <Pill label="Verdict" value={verifier.valid} />
        <Pill label="Rule" value={verifier.rule} />
        <Pill label="Gemini" value={verifier.gemini} />
      </div>
      <p className="line-clamp-3 text-[11px] leading-relaxed text-slate-600">{verifier.reason}</p>
    </div>
  )
}
