import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useDragControls, useMotionValue } from 'framer-motion'

function DetailList({ items }) {
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {items.filter(Boolean).map((item, i) => (
        <li key={i} style={{ borderRadius: 6, background: '#f8fafc', padding: '4px 8px', fontSize: 12, color: '#334155' }}>
          {item}
        </li>
      ))}
    </ul>
  )
}

function MathBlock({ label, formula }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <p style={{ margin: 0, fontSize: 13, color: '#475569', lineHeight: 1.6 }}>{label}</p>
      <code style={{
        display: 'block', borderRadius: 6,
        background: '#f1f5f9', padding: '8px 10px',
        fontSize: 11.5, color: '#334155', fontFamily: 'monospace',
        whiteSpace: 'pre-wrap', wordBreak: 'break-all',
      }}>
        {formula}
      </code>
    </div>
  )
}

export function buildInspectorMap(data) {
  const populationDemands = data.state.population_demands
  const affectedPopulation =
    data.state.estimated_affected_population ??
    populationDemands?.estimated_affected_population

  const populationDetail = populationDemands
    ? `raster population: ${affectedPopulation?.toLocaleString() ?? 'unknown'} affected / ${populationDemands.demand_level ?? 'unknown'} demand / source: ${populationDemands.source ?? 'unknown'}`
    : 'raster population: not available'

  const bestRoute = data.state.best_route
  function formatRoute(route) {
    const distanceKm =
      typeof route?.distance_km === 'number' ? route.distance_km
      : typeof route?.distance_m === 'number' ? route.distance_m / 1000
      : typeof route?.distance === 'number' ? route.distance / 1000
      : null
    const durationMin =
      typeof route?.duration_min === 'number' ? route.duration_min
      : typeof route?.duration_s === 'number' ? route.duration_s / 60
      : typeof route?.duration === 'number' ? route.duration / 60
      : null
    if (distanceKm == null || durationMin == null) return null
    return `${distanceKm.toFixed(2)} km / ${durationMin.toFixed(1)} min`
  }
  const bestRouteStats = formatRoute(bestRoute)
  const bestRouteDetail = bestRouteStats
    ? `best route: ${bestRoute.hospital ?? 'selected hospital'} / ${bestRouteStats}`
    : 'best route: not available'
  const blockedRoutes = data.state.blocked_routes.filter(Boolean)
  const blockedRoutesDetail = blockedRoutes.length
    ? `blocked routes: ${blockedRoutes.join(', ')}`
    : 'blocked routes: No routes are blocked'

  return {
    input: {
      title: 'Emergency Input Context',
      accent: '#6366f1', accentBg: '#eef2ff', glow: 'rgba(99,102,241,0.2)',
      summary: 'encoding',
      sections: {
        overview: <p style={{ margin: 0 }}>Raw emergency text is chunked into context units to seed downstream reasoning stages.</p>,
        details: <DetailList items={data.message.split(/[,.]/).filter(Boolean)} />,
        math: <MathBlock label="Message is split into emergency facts, preserving location, casualty, shelter, and routing signals for downstream stages." formula="chunks = split(message, /[,.!?]/)\ncontext = normalize(location + urgency + needs)\nstate_0 = { message, context }" />,
      },
    },
    router: {
      title: 'Router',
      accent: '#0ea5e9', accentBg: '#e0f2fe', glow: 'rgba(14,165,233,0.2)',
      summary: 'task routing',
      sections: {
        overview: <p style={{ margin: 0 }}>Router selects operational tasks from encoded context.</p>,
        details: <DetailList items={data.router.scores.map((row) => `${row.task}: ${(row.score * 100).toFixed(1)}%`)} />,
        math: <MathBlock label="Task routing combines classifier scores with emergency keywords so medical, shelter, and route work cannot be dropped from a mixed incident." formula="scores = classifier(context)\ntasks = { t | score(t) >= threshold }\nif medical_terms: tasks += hospital + ambulance\nif shelter_terms: tasks += shelter_allocation\nif route_terms: tasks += route_planning" />,
      },
    },
    planner: {
      title: 'Planner',
      accent: '#10b981', accentBg: '#d1fae5', glow: 'rgba(16,185,129,0.2)',
      summary: 'node priority',
      sections: {
        overview: <p style={{ margin: 0 }}>Planner prioritizes reasoning nodes for execution ordering.</p>,
        details: <DetailList items={data.planner.scores.map((row) => `${row.node}: ${(row.score * 100).toFixed(1)}%`)} />,
        math: <MathBlock label="Planner expands routed tasks into executable nodes, then orders high-risk operations before reporting and verification." formula="nodes = expand(tasks)\npriority(node) = severity_weight + dependency_weight\nplan = sort(nodes, priority desc)" />,
      },
    },
    slr: {
      title: 'SLR Graph',
      accent: '#f59e0b', accentBg: '#fef3c7', glow: 'rgba(245,158,11,0.2)',
      summary: 'topo sort',
      sections: {
        overview: <p style={{ margin: 0 }}>Dependency graph resolves stage order and execution compatibility.</p>,
        details: <DetailList items={data.slr.order.map((nodeId, i) => `#${i + 1} execution slot -> ${nodeId}`)} />,
        math: <MathBlock label="SLR builds a dependency graph so route scans, hospital lookup, ambulance dispatch, and shelter allocation run in a valid order." formula="G = (V, E)\nE includes: collect_sensor_data -> identify_alternative_routes\nE includes: identify_nearest_hospitals -> dispatch_ambulances\norder = topological_sort(G)" />,
      },
    },
    executor: {
      title: 'Executor',
      accent: '#8b5cf6', accentBg: '#ede9fe', glow: 'rgba(139,92,246,0.2)',
      summary: 'step execution',
      sections: {
        overview: <p style={{ margin: 0 }}>Executor applies the plan and tracks each operational step.</p>,
        details: <DetailList items={data.executor.timeline.map((item) => `Step ${item.step}: ${item.node} (${item.status})`)} />,
        math: <MathBlock label="Executor applies each tool result to the tracked emergency state and records completed, skipped, or failed steps in the timeline." formula="for node in order:\n  result = run_tool(node, state_t)\n  state_t+1 = merge(state_t, result.updates)\n  timeline += { node, status, result }" />,
      },
    },
    verifier: {
      title: 'Verifier',
      accent: '#ef4444', accentBg: '#fee2e2', glow: 'rgba(239,68,68,0.2)',
      summary: 'validation',
      sections: {
        overview: <p style={{ margin: 0 }}>Verifier validates safety rules and model-level consistency.</p>,
        details: <DetailList items={[
          `valid: ${String(data.verifier.valid)}`,
          `rule: ${String(data.verifier.rule)}`,
          `gemini: ${String(data.verifier.gemini)}`,
          data.verifier.reason,
        ]} />,
        math: <MathBlock label="Verifier fuses deterministic safety rules with the local Ollama model check; depleted but nonnegative resources are allowed after dispatch." formula="rule_ok = ambulances >= 0 AND shelters >= 0\nmodel_ok = ollama_validate(trace, final_state)\nvalid = rule_ok AND model_ok" />,
      },
    },
    final: {
      title: 'Final State',
      accent: '#14b8a6', accentBg: '#ccfbf1', glow: 'rgba(20,184,166,0.2)',
      summary: 'output state',
      sections: {
        overview: <p style={{ margin: 0 }}>Derived response state is emitted for operators and routing systems.</p>,
        details: <DetailList items={[
          `ambulances: ${data.state.ambulances}`,
          `shelters: ${data.state.shelters}`,
          populationDetail,
          blockedRoutesDetail,
          bestRouteDetail,
        ]} />,
        math: <MathBlock label="Final state is derived from real tool outputs: nearby hospital candidates, Dijkstra/OSRM route costs, blocked-route scan results, and resource allocation counts." formula={`hospitals = nearest(event_coordinates, hospital_index)\nblocked_edges = scan_roads(event_coordinates)\nif blocked_edges is empty: blocked_routes = []\nbest_route = min(Dijkstra(graph, event, hospital) for hospital in hospitals)\nstate* = { hospitals, best_route, blocked_routes, ambulances, shelters }\n${bestRouteDetail}`} />,
      },
    },
  }
}

const PANEL_W = 500
const PANEL_H_EST = 480
const MARGIN = 20
const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'details', label: 'Details' },
  { key: 'math', label: 'Internals' },
]

function computePlacement({ nodeScreenX, nodeScreenY, nodeW, nodeH }) {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const panelW = Math.min(PANEL_W, vw - MARGIN * 2)
  const openAbove = nodeScreenY > vh * 0.55
  const rawLeft = nodeScreenX - panelW / 2
  const left = Math.max(MARGIN, Math.min(rawLeft, vw - panelW - MARGIN))
  const gap = 18
  let top
  if (openAbove) {
    top = nodeScreenY - (nodeH ?? 0) / 2 - PANEL_H_EST - gap
  } else {
    top = nodeScreenY + (nodeH ?? 0) / 2 + gap
  }
  top = Math.max(MARGIN, Math.min(top, vh - PANEL_H_EST - MARGIN))
  const originX = (nodeScreenX - left) / panelW
  const originY = openAbove ? 1 : 0
  const initY = openAbove ? 14 : -14
  return { left, top, originX, originY, initY, panelW }
}

export function PhaseInspector({
  open,
  phaseTitle,
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

  const displayStageTitle = stageTitle ?? phaseTitle ?? ''

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
  }, [open, nodeScreenX, nodeScreenY, displayStageTitle, dragX, dragY])

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
  }, [open, activeTab, displayStageTitle])

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

          <motion.div
            key="panel"
            ref={(el) => {
              panelRef.current = el
              if (el) {
                panelHeightRef.current = el.offsetHeight
                setPanelSize({ width: el.offsetWidth || PANEL_W, height: el.offsetHeight || PANEL_H_EST })
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
            <div style={{
              position: 'absolute', inset: 0, top: 0, height: 120, pointerEvents: 'none',
              background: `radial-gradient(ellipse at top left, ${stageAccent}22 0%, transparent 60%)`,
            }} />

            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: 3,
              background: `linear-gradient(90deg, ${stageAccent}, ${stageAccent}44, transparent)`,
            }} />

            <div
              style={{ padding: '22px 24px 16px', position: 'relative', cursor: dragging ? 'grabbing' : 'grab', userSelect: 'none', WebkitUserSelect: 'none' }}
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
                    {displayStageTitle}
                  </h3>
                  {stageSummary && (
                    <div style={{ marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 6, background: stageAccentBg, border: `1px solid ${stageAccent}30`, borderRadius: 20, padding: '4px 12px' }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: stageAccent, display: 'inline-block', boxShadow: `0 0 0 3px ${stageGlow}` }} />
                      <span style={{ fontSize: 12.5, fontWeight: 500, color: stageAccent }}>{stageSummary}</span>
                    </div>
                  )}
                </div>
                <button
                  onClick={onClose}
                  style={{
                    flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    width: 34, height: 34, borderRadius: 10,
                    border: `1px solid ${stageAccent}25`,
                    background: stageAccentBg, color: stageAccent, cursor: 'pointer',
                    transition: 'all 0.15s ease', outline: 'none',
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

            <div style={{ padding: '0 24px 14px', position: 'relative' }}>
              <div style={{ display: 'inline-flex', gap: 2, background: '#f1f5f9', border: '1px solid #e8edf3', borderRadius: 14, padding: 4 }}>
                {TABS.map((t) => {
                  const isActive = activeTab === t.key
                  return (
                    <button
                      key={t.key}
                      onClick={() => onTabChange(t.key)}
                      style={{
                        position: 'relative', padding: '6px 16px', borderRadius: 10,
                        border: 'none', cursor: 'pointer', fontSize: 13,
                        fontWeight: isActive ? 600 : 500,
                        color: isActive ? '#fff' : '#64748b',
                        background: 'transparent',
                        transition: 'color 0.18s ease', outline: 'none', zIndex: 1,
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

            <div style={{ padding: '0 24px 24px', position: 'relative' }}>
              <div style={{ borderRadius: 16, border: '1px solid #e8edf3', background: 'linear-gradient(to bottom, #f8fafc, #ffffff)', overflow: 'hidden' }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
                    style={{
                      padding: '18px 20px', fontSize: 14, lineHeight: 1.75, color: '#334155',
                      maxHeight: 240, overflowY: 'auto', scrollbarWidth: 'thin',
                    }}
                  >
                    {sections?.[activeTab] ?? (
                      <p style={{ margin: 0, color: '#94a3b8', fontStyle: 'italic' }}>No content available.</p>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 24px 16px', borderTop: '1px solid #f1f5f9' }}>
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

export function PhaseInspectorModal(props) {
  const nodeScreenX =
    props.nodeScreenX ??
    (typeof window !== 'undefined' ? window.innerWidth / 2 : 720)
  const nodeScreenY =
    props.nodeScreenY ??
    (typeof window !== 'undefined' ? window.innerHeight / 2 : 450)

  return (
    <PhaseInspector
      {...props}
      nodeScreenX={nodeScreenX}
      nodeScreenY={nodeScreenY}
      nodeW={props.nodeW ?? 0}
      nodeH={props.nodeH ?? 0}
    />
  )
}
