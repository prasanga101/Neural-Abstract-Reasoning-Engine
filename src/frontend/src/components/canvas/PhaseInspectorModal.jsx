import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useDragControls, useMotionValue } from 'framer-motion'

// ─── Constants ────────────────────────────────────────────────────────────────

const PANEL_W = 500
const PANEL_H_EST = 480
const MARGIN = 20
const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'details', label: 'Details' },
  { key: 'math', label: 'Internals' },
]

// ─── Placement logic ──────────────────────────────────────────────────────────
// Given the node's screen-space center, find the best quadrant to open the
// inspector so it stays fully visible and feels tethered to the node.

function computePlacement({ nodeScreenX, nodeScreenY, nodeW, nodeH }) {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const panelW = Math.min(PANEL_W, vw - MARGIN * 2)

  // Decide vertical: prefer above if node is in the lower 55% of viewport
  const openAbove = nodeScreenY > vh * 0.55

  // Decide horizontal: align panel so it's roughly centered on the node,
  // but clamp to stay inside the viewport
  const rawLeft = nodeScreenX - panelW / 2
  const left = Math.max(MARGIN, Math.min(rawLeft, vw - panelW - MARGIN))

  // Vertical position
  const gap = 18
  let top
  if (openAbove) {
    top = nodeScreenY - (nodeH ?? 0) / 2 - PANEL_H_EST - gap
  } else {
    top = nodeScreenY + (nodeH ?? 0) / 2 + gap
  }
  top = Math.max(MARGIN, Math.min(top, vh - PANEL_H_EST - MARGIN))

  // Animation origin: which corner/edge the panel grows from
  const originX = (nodeScreenX - left) / panelW  // 0..1
  const originY = openAbove ? 1 : 0

  // Initial offset for enter/exit animation
  const initY = openAbove ? 14 : -14

  return { left, top, originX, originY, initY, panelW }
}

// ─── PhaseInspector ───────────────────────────────────────────────────────────

export function PhaseInspector({
  open,
  stageTitle,
  stageAccent = '#6366f1',
  stageAccentBg = '#eef2ff',
  stageGlow = 'rgba(99,102,241,0.2)',
  stageSummary = '',
  activeTab,
  onTabChange,
  onClose,
  sections = {},
  nodeScreenX,
  nodeScreenY,
  nodeW,
  nodeH,
}) {
  const panelRef = useRef(null)
  const panelHeightRef = useRef(PANEL_H_EST)
  const dragControls = useDragControls()
  const [dragging, setDragging] = useState(false)
  const [panelSize, setPanelSize] = useState({ width: PANEL_W, height: PANEL_H_EST })
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1440,
    height: typeof window !== 'undefined' ? window.innerHeight : 900,
  })
  const dragX = useMotionValue(0)
  const dragY = useMotionValue(0)

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    dragX.set(0)
    dragY.set(0)
    setDragging(false)
  }, [open, nodeScreenX, nodeScreenY, stageTitle, dragX, dragY])

  useLayoutEffect(() => {
    if (!open) return undefined

    const updateMetrics = () => {
      setViewport({ width: window.innerWidth, height: window.innerHeight })
      if (panelRef.current) {
        const nextWidth = panelRef.current.offsetWidth || PANEL_W
        const nextHeight = panelRef.current.offsetHeight || PANEL_H_EST
        panelHeightRef.current = nextHeight
        setPanelSize({ width: nextWidth, height: nextHeight })
      }
    }

    updateMetrics()
    window.addEventListener('resize', updateMetrics)
    return () => window.removeEventListener('resize', updateMetrics)
  }, [open, activeTab, stageTitle])

  if (!open || nodeScreenX == null) return null

  const placement = computePlacement({ nodeScreenX, nodeScreenY, nodeW, nodeH })
  const dragConstraints = {
    left: MARGIN - placement.left,
    top: MARGIN - placement.top,
    right: viewport.width - placement.left - panelSize.width - MARGIN,
    bottom: viewport.height - placement.top - panelSize.height - MARGIN,
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Soft backdrop — dim canvas but not aggressively */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: 'fixed', inset: 0, zIndex: 9997,
              background: 'rgba(15, 23, 42, 0.12)',
              backdropFilter: 'blur(2px)',
            }}
          />

          {/* Panel */}
          <motion.div
            key="panel"
            ref={(el) => {
              panelRef.current = el
              if (el) {
                panelHeightRef.current = el.offsetHeight
                setPanelSize({
                  width: el.offsetWidth || PANEL_W,
                  height: el.offsetHeight || PANEL_H_EST,
                })
              }
            }}
            initial={{ opacity: 0, scale: 0.94, y: placement.initY }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: placement.initY }}
            transition={{ duration: 0.3, ease: [0.22, 0.61, 0.36, 1] }}
            drag
            dragControls={dragControls}
            dragListener={false}
            dragConstraints={dragConstraints}
            dragMomentum={false}
            dragElastic={0}
            onDragStart={() => setDragging(true)}
            onDragEnd={() => setDragging(false)}
            whileDrag={{
              scale: 1.01,
              boxShadow: `0 0 0 1px ${stageAccent}14, 0 36px 90px rgba(15,23,42,0.24), 0 16px 36px rgba(15,23,42,0.12)`,
            }}
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              left: placement.left,
              top: placement.top,
              width: placement.panelW,
              x: dragX,
              y: dragY,
              zIndex: 9999,
              transformOrigin: `${placement.originX * 100}% ${placement.originY * 100}%`,
              borderRadius: 24,
              background: 'rgba(255, 255, 255, 0.97)',
              border: `1.5px solid ${stageAccent}30`,
              boxShadow: `0 0 0 1px ${stageAccent}14, 0 32px 80px rgba(15,23,42,0.22), 0 12px 32px rgba(15,23,42,0.10)`,
              overflow: 'hidden',
            }}
          >
            {/* Top gradient wash */}
            <div style={{
              position: 'absolute', inset: 0, top: 0, height: 120, pointerEvents: 'none',
              background: `radial-gradient(ellipse at top left, ${stageAccent}22 0%, transparent 60%)`,
            }} />

            {/* Accent top line */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: 3,
              background: `linear-gradient(90deg, ${stageAccent}, ${stageAccent}44, transparent)`,
            }} />

            {/* ── Header ── */}
            <div
              style={{
                padding: '22px 24px 16px',
                position: 'relative',
                cursor: dragging ? 'grabbing' : 'grab',
                userSelect: 'none',
                WebkitUserSelect: 'none',
              }}
              onPointerDown={(event) => {
                if (event.target.closest('button')) return
                dragControls.start(event)
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: 0, fontSize: 10, fontWeight: 600, letterSpacing: '0.18em', textTransform: 'uppercase', color: '#94a3b8' }}>
                    Phase Inspector
                  </p>
                  <h3 style={{ margin: '6px 0 0', fontSize: 26, fontWeight: 700, letterSpacing: '-0.03em', color: stageAccent, lineHeight: 1.1 }}>
                    {stageTitle}
                  </h3>
                  {stageSummary && (
                    <div style={{ marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 6, background: stageAccentBg, border: `1px solid ${stageAccent}30`, borderRadius: 20, padding: '4px 12px' }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: stageAccent, display: 'inline-block', boxShadow: `0 0 0 3px ${stageGlow}` }} />
                      <span style={{ fontSize: 12.5, fontWeight: 500, color: stageAccent }}>{stageSummary}</span>
                    </div>
                  )}
                </div>

                {/* Close */}
                <button
                  onClick={onClose}
                  style={{
                    flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    width: 34, height: 34, borderRadius: 10,
                    border: `1px solid ${stageAccent}25`,
                    background: stageAccentBg,
                    color: stageAccent, cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    outline: 'none',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = stageAccent; e.currentTarget.style.color = '#fff' }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = stageAccentBg; e.currentTarget.style.color = stageAccent }}
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                    <line x1="1" y1="1" x2="11" y2="11" /><line x1="11" y1="1" x2="1" y2="11" />
                  </svg>
                </button>
              </div>
            </div>

            {/* ── Tabs ── */}
            <div style={{ padding: '0 24px 14px', position: 'relative' }}>
              <div style={{
                display: 'inline-flex', gap: 2,
                background: '#f1f5f9',
                border: '1px solid #e8edf3',
                borderRadius: 14, padding: 4,
              }}>
                {TABS.map((t) => {
                  const isActive = activeTab === t.key
                  return (
                    <button
                      key={t.key}
                      onClick={() => onTabChange(t.key)}
                      style={{
                        position: 'relative',
                        padding: '6px 16px',
                        borderRadius: 10,
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: isActive ? 600 : 500,
                        color: isActive ? '#fff' : '#64748b',
                        background: 'transparent',
                        transition: 'color 0.18s ease',
                        outline: 'none',
                        zIndex: 1,
                      }}
                    >
                      {isActive && (
                        <motion.span
                          layoutId="inspector-tab-bg"
                          style={{
                            position: 'absolute', inset: 0, borderRadius: 10,
                            background: stageAccent,
                            boxShadow: `0 4px 14px ${stageGlow}`,
                            zIndex: -1,
                          }}
                          transition={{ type: 'spring', stiffness: 340, damping: 28 }}
                        />
                      )}
                      {t.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* ── Content ── */}
            <div style={{ padding: '0 24px 24px', position: 'relative' }}>
              <div style={{
                borderRadius: 16,
                border: '1px solid #e8edf3',
                background: 'linear-gradient(to bottom, #f8fafc, #ffffff)',
                overflow: 'hidden',
              }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
                    style={{
                      padding: '18px 20px',
                      fontSize: 14,
                      lineHeight: 1.75,
                      color: '#334155',
                      maxHeight: 240,
                      overflowY: 'auto',
                      scrollbarWidth: 'thin',
                    }}
                  >
                    {sections?.[activeTab] ?? (
                      <p style={{ margin: 0, color: '#94a3b8', fontStyle: 'italic' }}>No content available.</p>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>

            {/* ── Footer ── */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 24px 16px',
              borderTop: '1px solid #f1f5f9',
            }}>
              <span style={{ fontSize: 10.5, color: '#b0bccb', letterSpacing: '0.03em', display: 'flex', alignItems: 'center', gap: 5 }}>
                <kbd style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 22, height: 16, background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 4, fontSize: 9, color: '#94a3b8', fontFamily: 'inherit' }}>esc</kbd>
                to close · click canvas to dismiss
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: stageAccent, opacity: 0.7 }} />
                <span style={{ fontSize: 10.5, color: '#94a3b8', fontWeight: 500 }}>NARE</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
