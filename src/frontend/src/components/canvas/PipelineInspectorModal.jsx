import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useDragControls, useMotionValue } from 'framer-motion'

const PANEL_W = 920
const PANEL_H_EST = 620
const MARGIN = 24
const MIN_PANEL_W = 720
const MIN_PANEL_H = 480
const RESIZE_HANDLES = [
  { key: 'n', cursor: 'ns-resize', style: { top: -6, left: 24, right: 24, height: 12 } },
  { key: 's', cursor: 'ns-resize', style: { bottom: -6, left: 24, right: 24, height: 12 } },
  { key: 'e', cursor: 'ew-resize', style: { top: 24, right: -6, bottom: 24, width: 12 } },
  { key: 'w', cursor: 'ew-resize', style: { top: 24, left: -6, bottom: 24, width: 12 } },
  { key: 'ne', cursor: 'nesw-resize', style: { top: -6, right: -6, width: 16, height: 16 } },
  { key: 'nw', cursor: 'nwse-resize', style: { top: -6, left: -6, width: 16, height: 16 } },
  { key: 'se', cursor: 'nwse-resize', style: { bottom: -6, right: -6, width: 16, height: 16 } },
  { key: 'sw', cursor: 'nesw-resize', style: { bottom: -6, left: -6, width: 16, height: 16 } },
]
const SECTION_TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'details', label: 'Details' },
  { key: 'math', label: 'Internals' },
]

function clampValue(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export function PipelineInspectorModal({
  open,
  phases,
  activePhaseId,
  onPhaseChange,
  onClose,
  sections,
}) {
  const panelRef = useRef(null)
  const panelHeightRef = useRef(PANEL_H_EST)
  const resizeStateRef = useRef(null)
  const dragControls = useDragControls()
  const [dragging, setDragging] = useState(false)
  const [resizing, setResizing] = useState(false)
  const [activeSectionTab, setActiveSectionTab] = useState('overview')
  const [panelSize, setPanelSize] = useState({ width: PANEL_W, height: PANEL_H_EST })
  const [desiredSize, setDesiredSize] = useState({ width: PANEL_W, height: PANEL_H_EST })
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1440,
    height: typeof window !== 'undefined' ? window.innerHeight : 900,
  })
  const dragX = useMotionValue(0)
  const dragY = useMotionValue(0)

  const activePhase = phases.find((phase) => phase.id === activePhaseId) ?? phases[0]
  const activeSections = sections?.[activePhaseId] || {}
  const accent = activePhase.accent ?? '#6366f1'
  const accentBg = activePhase.accentBg ?? '#eef2ff'
  const accentGlow = activePhase.accentGlow ?? 'rgba(99,102,241,0.2)'

  useEffect(() => {
    if (!open) return
    const handler = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    dragX.set(0)
    dragY.set(0)
    setDragging(false)
    setResizing(false)
    setDesiredSize({ width: PANEL_W, height: PANEL_H_EST })
  }, [open, dragX, dragY])

  useEffect(() => {
    setActiveSectionTab('overview')
  }, [activePhaseId])

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
  }, [open, activePhaseId, activeSectionTab])

  useEffect(() => {
    if (!open || !resizing) return undefined

    const handlePointerMove = (event) => {
      const resizeState = resizeStateRef.current
      if (!resizeState) return

      const dx = event.clientX - resizeState.startX
      const dy = event.clientY - resizeState.startY
      const currentLeft = resizeState.baseLeft + resizeState.startDragX
      const currentTop = resizeState.baseTop + resizeState.startDragY
      const currentRight = currentLeft + resizeState.startWidth
      const currentBottom = currentTop + resizeState.startHeight

      let nextWidth = resizeState.startWidth
      let nextHeight = resizeState.startHeight
      let nextDragX = resizeState.startDragX
      let nextDragY = resizeState.startDragY

      if (resizeState.handle.includes('e')) {
        const maxWidth = viewport.width - currentLeft - MARGIN
        nextWidth = clampValue(resizeState.startWidth + dx, MIN_PANEL_W, maxWidth)
      }

      if (resizeState.handle.includes('s')) {
        const maxHeight = viewport.height - currentTop - MARGIN
        nextHeight = clampValue(resizeState.startHeight + dy, MIN_PANEL_H, maxHeight)
      }

      if (resizeState.handle.includes('w')) {
        const maxWidth = currentRight - MARGIN
        nextWidth = clampValue(resizeState.startWidth - dx, MIN_PANEL_W, maxWidth)
        nextDragX = resizeState.startDragX + (resizeState.startWidth - nextWidth)
      }

      if (resizeState.handle.includes('n')) {
        const maxHeight = currentBottom - MARGIN
        nextHeight = clampValue(resizeState.startHeight - dy, MIN_PANEL_H, maxHeight)
        nextDragY = resizeState.startDragY + (resizeState.startHeight - nextHeight)
      }

      dragX.set(nextDragX)
      dragY.set(nextDragY)
      setDesiredSize({ width: nextWidth, height: nextHeight })
    }

    const stopResize = () => {
      resizeStateRef.current = null
      setResizing(false)
    }

    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', stopResize)

    return () => {
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', stopResize)
    }
  }, [open, resizing, viewport.height, viewport.width])

  if (!open || !activePhase) return null

  const maxWidth = viewport.width - MARGIN * 2
  const maxHeight = viewport.height - 86 - MARGIN
  const clampedWidth = Math.min(maxWidth, Math.max(MIN_PANEL_W, desiredSize.width))
  const clampedHeight = Math.min(maxHeight, Math.max(MIN_PANEL_H, desiredSize.height))
  const initialWidth = Math.min(PANEL_W, viewport.width - MARGIN * 2)
  const baseLeft = Math.max(MARGIN, viewport.width - initialWidth - MARGIN)
  const baseTop = 86
  const dragConstraints = {
    left: MARGIN - baseLeft,
    top: MARGIN - baseTop,
    right: viewport.width - baseLeft - clampedWidth - MARGIN,
    bottom: viewport.height - baseTop - clampedHeight - MARGIN,
  }

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.div
            key="pipeline-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 10000,
              background: 'rgba(15, 23, 42, 0.12)',
              backdropFilter: 'blur(2px)',
            }}
          />

          <motion.div
            key="pipeline-panel"
            ref={(element) => {
              panelRef.current = element
              if (element) {
                panelHeightRef.current = element.offsetHeight
                setPanelSize({
                  width: element.offsetWidth || PANEL_W,
                  height: element.offsetHeight || PANEL_H_EST,
                })
              }
            }}
            initial={{ opacity: 0, scale: 0.96, y: -12, x: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -12, x: 10 }}
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
              boxShadow: `0 0 0 1px ${accent}14, 0 36px 90px rgba(15,23,42,0.24), 0 16px 36px rgba(15,23,42,0.12)`,
            }}
            onClick={(event) => event.stopPropagation()}
            style={{
              position: 'fixed',
              left: baseLeft,
              top: baseTop,
              width: clampedWidth,
              height: clampedHeight,
              x: dragX,
              y: dragY,
              zIndex: 10001,
              borderRadius: 24,
              background: 'rgba(255, 255, 255, 0.97)',
              border: `1.5px solid ${accent}30`,
              boxShadow: `0 0 0 1px ${accent}14, 0 32px 80px rgba(15,23,42,0.22), 0 12px 32px rgba(15,23,42,0.10)`,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                position: 'absolute',
                inset: 0,
                top: 0,
                height: 120,
                pointerEvents: 'none',
                background: `radial-gradient(ellipse at top left, ${accent}22 0%, transparent 60%)`,
              }}
            />

            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: `linear-gradient(90deg, ${accent}, ${accent}44, transparent)`,
              }}
            />

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
                    Pipeline Inspector
                  </p>
                  <h3 style={{ margin: '6px 0 0', fontSize: 26, fontWeight: 700, letterSpacing: '-0.03em', color: accent, lineHeight: 1.1 }}>
                    {activePhase.title}
                  </h3>
                </div>

                <button
                  onClick={onClose}
                  style={{
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 34,
                    height: 34,
                    borderRadius: 10,
                    border: `1px solid ${accent}25`,
                    background: accentBg,
                    color: accent,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    outline: 'none',
                  }}
                  onMouseEnter={(event) => {
                    event.currentTarget.style.background = accent
                    event.currentTarget.style.color = '#fff'
                  }}
                  onMouseLeave={(event) => {
                    event.currentTarget.style.background = accentBg
                    event.currentTarget.style.color = accent
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                    <line x1="1" y1="1" x2="11" y2="11" />
                    <line x1="11" y1="1" x2="1" y2="11" />
                  </svg>
                </button>
              </div>
            </div>

            <div style={{ padding: '0 24px 14px', position: 'relative' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {phases.map((phase) => {
                  const isActive = phase.id === activePhase.id
                  return (
                    <button
                      key={phase.id}
                      type="button"
                      onClick={() => onPhaseChange(phase.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '6px 14px',
                        borderRadius: 999,
                        border: `1px solid ${isActive ? phase.accent : '#e2e8f0'}`,
                        background: isActive ? phase.accentBg : '#ffffff',
                        color: isActive ? phase.accent : '#64748b',
                        fontSize: 12.5,
                        fontWeight: isActive ? 600 : 500,
                        cursor: 'pointer',
                        transition: 'all 0.18s ease',
                      }}
                      >
                      <span
                        style={{
                          width: 7,
                          height: 7,
                          borderRadius: '50%',
                          background: isActive ? phase.accent ?? accent : '#94a3b8',
                          boxShadow: isActive
                            ? `0 0 0 4px ${phase.accentGlow ?? accentGlow}`
                            : 'none',
                        }}
                      />
                      {phase.title}
                    </button>
                  )
                })}
              </div>
            </div>

            <div style={{ padding: '0 24px 14px', position: 'relative' }}>
              <div style={{
                display: 'inline-flex',
                gap: 2,
                background: '#f1f5f9',
                border: '1px solid #e8edf3',
                borderRadius: 14,
                padding: 4,
              }}>
                {SECTION_TABS.map((tab) => {
                  const isActive = activeSectionTab === tab.key
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveSectionTab(tab.key)}
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
                      {isActive ? (
                        <motion.span
                          layoutId="pipeline-inspector-section-tab"
                          style={{
                            position: 'absolute',
                            inset: 0,
                            borderRadius: 10,
                            background: accent,
                            boxShadow: `0 4px 14px ${accentGlow}`,
                            zIndex: -1,
                          }}
                          transition={{ type: 'spring', stiffness: 340, damping: 28 }}
                        />
                      ) : null}
                      {tab.label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div style={{ padding: '0 24px 24px', position: 'relative' }}>
              <div style={{
                borderRadius: 16,
                border: '1px solid #e8edf3',
                background: 'linear-gradient(to bottom, #f8fafc, #ffffff)',
                overflow: 'hidden',
              }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`${activePhase.id}-${activeSectionTab}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
                    style={{
                      padding: '18px 20px',
                      fontSize: 14,
                      lineHeight: 1.75,
                      color: '#334155',
                      maxHeight: Math.max(180, clampedHeight - 280),
                      overflowY: 'auto',
                      scrollbarWidth: 'thin',
                    }}
                  >
                    <div>
                      {activeSectionTab === 'overview' && activeSections.overview}
                      {activeSectionTab === 'details' && activeSections.details}
                      {activeSectionTab === 'math' && activeSections.math}
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 24px 16px',
              borderTop: '1px solid #f1f5f9',
            }}>
              <span style={{ fontSize: 10.5, color: '#b0bccb', letterSpacing: '0.03em', display: 'flex', alignItems: 'center', gap: 5 }}>
                <kbd style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 22, height: 16, background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 4, fontSize: 9, color: '#94a3b8', fontFamily: 'inherit' }}>esc</kbd>
                to close · drag the header to reposition
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: accent, opacity: 0.7 }} />
                <span style={{ fontSize: 10.5, color: '#94a3b8', fontWeight: 500 }}>NARE</span>
              </div>
            </div>

            <button
              type="button"
              aria-label="Resize handle ornament"
              tabIndex={-1}
              style={{
                position: 'absolute',
                right: 10,
                bottom: 10,
                width: 18,
                height: 18,
                padding: 0,
                border: 'none',
                background: 'transparent',
                pointerEvents: 'none',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 6,
                  background: 'linear-gradient(135deg, transparent 0 40%, rgba(148,163,184,0.22) 40% 58%, rgba(100,116,139,0.42) 58% 74%, rgba(71,85,105,0.7) 74% 100%)',
                }}
              />
            </button>

            {RESIZE_HANDLES.map((handle) => (
              <button
                key={handle.key}
                type="button"
                aria-label={`Resize from ${handle.key}`}
                onPointerDown={(event) => {
                  event.preventDefault()
                  event.stopPropagation()
                  resizeStateRef.current = {
                    handle: handle.key,
                    startX: event.clientX,
                    startY: event.clientY,
                    startWidth: clampedWidth,
                    startHeight: clampedHeight,
                    startDragX: dragX.get(),
                    startDragY: dragY.get(),
                    baseLeft,
                    baseTop,
                  }
                  setResizing(true)
                }}
                style={{
                  position: 'absolute',
                  ...handle.style,
                  padding: 0,
                  border: 'none',
                  background: 'transparent',
                  cursor: handle.cursor,
                }}
              />
            ))}
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  )
}
