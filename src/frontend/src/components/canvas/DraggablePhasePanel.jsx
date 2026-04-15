import { useState } from 'react'
import { motion } from 'framer-motion'

export function DraggablePhasePanel({
  id,
  title,
  subtitle,
  initialPosition,
  stageIndex,
  visible,
  isHighlighted,
  dragConstraintsRef,
  onHover,
  onOpen,
  children,
  className = '',
  tone = 'slate',
}) {
  const [position, setPosition] = useState(initialPosition)

  const toneStyles = {
    slate: 'border-slate-200/80 bg-white/75',
    blue: 'border-blue-200/80 bg-blue-50/55',
    cyan: 'border-cyan-200/80 bg-cyan-50/55',
    emerald: 'border-emerald-200/80 bg-emerald-50/55',
    violet: 'border-violet-200/80 bg-violet-50/55',
    rose: 'border-rose-200/80 bg-rose-50/55',
  }

  return (
    <motion.article
      className={`absolute ${className}`}
      style={{ left: position.x, top: position.y }}
      drag
      dragConstraints={dragConstraintsRef}
      dragMomentum={false}
      onDragEnd={(_, info) => {
        setPosition((prev) => ({
          x: prev.x + info.offset.x,
          y: prev.y + info.offset.y,
        }))
      }}
      onMouseEnter={() => onHover(id)}
      onMouseLeave={() => onHover(null)}
      initial={{ opacity: 0, y: 20 }}
      animate={{
        opacity: visible ? 1 : 0.18,
        y: visible ? 0 : 14,
        scale: isHighlighted ? 1.01 : 1,
      }}
      transition={{ duration: 0.25, delay: stageIndex * 0.08 }}
    >
      <div
        className={`w-full cursor-grab rounded-2xl border p-3 shadow-[0_8px_28px_rgba(15,23,42,0.07)] backdrop-blur-md active:cursor-grabbing ${
          toneStyles[tone] || toneStyles.slate
        } ${
          isHighlighted
            ? 'ring-2 ring-blue-200/70'
            : ''
        }`}
      >
        <div className="mb-2 flex items-start justify-between gap-3">
          <div>
            <h4 className="text-sm font-semibold tracking-tight text-slate-900">{title}</h4>
            <p className="text-[11px] text-slate-500">{subtitle}</p>
          </div>
          <button
            type="button"
            className="rounded-full border border-slate-300/80 bg-white/70 px-2.5 py-1 text-[11px] text-slate-700 hover:bg-white"
            onClick={onOpen}
          >
            Inspect
          </button>
        </div>
        <div className="space-y-2">{children}</div>
      </div>
    </motion.article>
  )
}
