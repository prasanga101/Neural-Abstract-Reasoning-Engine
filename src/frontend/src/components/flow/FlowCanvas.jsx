import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { PIPELINE_PHASES } from '../../data/pipelinePhases'
import { buildPipelineSections, summarizeStage } from '../../data/pipelineDataAdapter'
import {
  Background,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { PhaseInspector } from '../canvas/PhaseInspectorModal'
import { PipelineInspectorModal } from '../canvas/PipelineInspectorModal'

// ─── Stage definitions ────────────────────────────────────────────────────────

const STAGES = [
  {
    id: 'input', title: 'Emergency Input', subtitle: 'Context ingestion',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    accent: '#3b82f6', accentBg: '#eff6ff', accentGlow: 'rgba(59,130,246,0.2)',
    x: 0, y: 186, width: 260, height: 132,
  },
  {
    id: 'router', title: 'Router', subtitle: 'Task classification',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
    accent: '#8b5cf6', accentBg: '#f5f3ff', accentGlow: 'rgba(139,92,246,0.2)',
    x: 324, y: 186, width: 260, height: 132,
  },
  {
    id: 'planner', title: 'Planner', subtitle: 'Node prioritisation',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
    accent: '#0ea5e9', accentBg: '#f0f9ff', accentGlow: 'rgba(14,165,233,0.2)',
    x: 648, y: 186, width: 260, height: 132,
  },
  {
    id: 'slr', title: 'SLR Graph', subtitle: 'Dependency resolution core',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
      </svg>
    ),
    accent: '#10b981', accentBg: '#ecfdf5', accentGlow: 'rgba(16,185,129,0.2)',
    x: 1006, y: 76, width: 430, height: 390,
  },
  {
    id: 'executor', title: 'Executor', subtitle: 'Step execution',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="5 3 19 12 5 21 5 3" />
      </svg>
    ),
    accent: '#f59e0b', accentBg: '#fffbeb', accentGlow: 'rgba(245,158,11,0.2)',
    x: 1498, y: 186, width: 260, height: 132,
  },
  {
    id: 'verifier', title: 'Verifier', subtitle: 'Policy validation',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    accent: '#ef4444', accentBg: '#fef2f2', accentGlow: 'rgba(239,68,68,0.2)',
    x: 1822, y: 186, width: 260, height: 132,
  },
  {
    id: 'final', title: 'Final State', subtitle: 'Dispatch output',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    ),
    accent: '#6366f1', accentBg: '#eef2ff', accentGlow: 'rgba(99,102,241,0.2)',
    x: 2146, y: 186, width: 260, height: 132,
  },
]

const STAGE_ORDER = STAGES.map((s) => s.id)
const EDGE_CHAIN = [
  ['input', 'router'], ['router', 'planner'], ['planner', 'slr'],
  ['slr', 'executor'], ['executor', 'verifier'], ['verifier', 'final'],
]
const getStageById = (id) => STAGES.find((s) => s.id === id)

// ─── Mini SLR graph ───────────────────────────────────────────────────────────

function MiniSlrGraph({ slr }) {
  const points = slr.nodes.map((node, i) => ({
    id: node.id, x: 26 + i * 34, y: i % 2 === 0 ? 38 : 82, label: node.label.slice(0, 5),
  }))
  const pointMap = Object.fromEntries(points.map((p) => [p.id, p]))
  return (
    <div style={{ marginTop: 10, height: 154, borderRadius: 12, border: '1.5px solid #6ee7b7', background: 'rgba(236,253,245,0.7)', overflow: 'hidden' }}>
      <svg viewBox="0 0 250 154" style={{ width: '100%', height: '100%' }}>
        <defs>
          <marker id="mini-arr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M2 2L8 5L2 8" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </marker>
        </defs>
        {slr.edges.map((edge, i) => {
          const s = pointMap[edge.source], t = pointMap[edge.target]
          if (!s || !t) return null
          const mx = (s.x + t.x) / 2
          return <path key={i} d={`M${s.x} ${s.y} C${mx} ${s.y},${mx} ${t.y},${t.x} ${t.y}`}
            fill="none" stroke="#34d399" strokeWidth="2" markerEnd="url(#mini-arr)" opacity="0.85" />
        })}
        {points.map((p) => (
          <g key={p.id} transform={`translate(${p.x},${p.y})`}>
            <circle r="11" fill="white" stroke="#10b981" strokeWidth="1.8" />
            <text textAnchor="middle" y="4.5" fontSize="7.5" fill="#065f46" fontWeight="500" style={{ userSelect: 'none' }}>{p.label}</text>
          </g>
        ))}
      </svg>
    </div>
  )
}

// ─── Stage node ───────────────────────────────────────────────────────────────

function StageNode({ data }) {
  const stage = getStageById(data.id)
  const isSlr = data.id === 'slr'
  const [hovered, setHovered] = useState(false)
  const isHighlighted = hovered || data.selected

  return (
    <>
      <Handle type="target" position={Position.Left} style={{ opacity: 0, pointerEvents: 'none' }} />
      <motion.div
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        initial={{ opacity: 0, y: 16 }}
        animate={{
          opacity: data.dimmed ? 0.36 : data.active ? 1 : 0.22,
          y: 0,
          scale: data.selected ? 1.03 : data.dimmed ? 0.982 : 1,
        }}
        transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
        style={{
          width: '100%', height: '100%',
          borderRadius: isSlr ? 22 : 18,
          background: data.selected
            ? `linear-gradient(150deg, ${stage.accentBg}, #ffffff 60%)`
            : '#ffffff',
          border: data.selected
            ? `2px solid ${stage.accent}`
            : `1.5px solid ${isHighlighted ? stage.accent + '55' : '#e8edf3'}`,
          boxShadow: data.selected
            ? `0 0 0 5px ${stage.accentGlow}, 0 20px 52px rgba(15,23,42,0.16)`
            : isHighlighted
              ? `0 0 0 3px ${stage.accentGlow}, 0 10px 28px rgba(15,23,42,0.10)`
              : data.active
                ? '0 6px 22px rgba(15,23,42,0.07)'
                : '0 2px 8px rgba(15,23,42,0.04)',
          filter: data.dimmed ? 'saturate(0.45) brightness(1.06)' : 'none',
          padding: isSlr ? '14px 14px 12px' : '14px 16px',
          cursor: 'pointer', position: 'relative', overflow: 'hidden',
          transition: 'box-shadow 0.22s ease, border-color 0.22s ease, filter 0.3s ease',
        }}
      >
        {/* Accent bar */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 3,
          background: `linear-gradient(90deg, ${stage.accent}, ${stage.accent}55)`,
          borderRadius: `${isSlr ? 22 : 18}px ${isSlr ? 22 : 18}px 0 0`,
          opacity: data.active ? 1 : 0.3, transition: 'opacity 0.3s',
        }} />

        {/* Active glow blob */}
        {(data.active || data.selected) && (
          <div style={{
            position: 'absolute', top: -28, right: -28, width: 110, height: 110,
            borderRadius: '50%', background: stage.accentGlow, filter: 'blur(24px)', pointerEvents: 'none',
          }} />
        )}

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4 }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            width: 40, height: 40, flexShrink: 0, borderRadius: 11,
            background: isHighlighted || data.selected ? stage.accent : stage.accentBg,
            color: isHighlighted || data.selected ? '#fff' : stage.accent,
            transition: 'background 0.2s, color 0.2s',
            boxShadow: data.selected ? `0 4px 14px ${stage.accentGlow}` : 'none',
          }}>
            {stage.icon}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ margin: 0, fontSize: 20, fontWeight: 650, letterSpacing: '-0.02em', color: '#0f172a', lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {data.title}
            </p>
            <p style={{ margin: '3px 0 0', fontSize: 14, color: '#94a3b8', lineHeight: 1.3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {stage.subtitle}
            </p>
          </div>
        </div>

        {/* Stat pill */}
        <div style={{
          marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 5,
          background: data.selected ? stage.accent + '18' : stage.accentBg,
          border: `1px solid ${stage.accent}${data.selected ? '44' : '22'}`,
          borderRadius: 20, padding: '4px 12px',
          fontSize: 14, fontWeight: 500, color: stage.accent,
        }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: data.active ? stage.accent : '#cbd5e1', flexShrink: 0, transition: 'background 0.3s' }} />
          {data.summary}
        </div>

        {isSlr && data.slr && <MiniSlrGraph slr={data.slr} />}

        <AnimatePresence>
          {data.justActivated && (
            <motion.div key="pulse"
              initial={{ opacity: 0.8, scale: 1 }} animate={{ opacity: 0, scale: 1.13 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.72, ease: 'easeOut' }}
              style={{ position: 'absolute', inset: -3, borderRadius: isSlr ? 25 : 21, border: `2.5px solid ${stage.accent}`, pointerEvents: 'none' }}
            />
          )}
        </AnimatePresence>
      </motion.div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0, pointerEvents: 'none' }} />
    </>
  )
}

const nodeTypes = { stage: StageNode }

// ─── Inner canvas ─────────────────────────────────────────────────────────────

function FlowCanvasInner({ data, runSignal, pipelineInspectorSignal }) {
  const { getViewport } = useReactFlow()
  const containerRef = useRef(null)

  const [hoveredNodeId, setHoveredNodeId] = useState(null)
  const [activeIndex, setActiveIndex] = useState(-1)
  const [justActivated, setJustActivated] = useState(null)
  const [inspector, setInspector] = useState(null)
  const [tab, setTab] = useState('overview')
  const [isPipelineInspectorOpen, setIsPipelineInspectorOpen] = useState(false)
  const [activePipelinePhaseId, setActivePipelinePhaseId] = useState('input')

  const selectedId = inspector?.id ?? null

  const makeNodes = useCallback(() =>
    STAGES.map((stage, i) => ({
      id: stage.id, type: 'stage',
      position: { x: stage.x, y: stage.y },
      data: { id: stage.id, title: stage.title, summary: summarizeStage(stage.id, data), slr: data.slr, active: false, selected: false, dimmed: false, justActivated: false },
      draggable: true, selectable: false,
      style: { width: stage.width, height: stage.height },
    })), [data]) // eslint-disable-line

  const [nodes, setNodes, onNodesChange] = useNodesState(makeNodes())
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    setNodes((prev) =>
      prev.map((node) => {
        const idx = STAGE_ORDER.indexOf(node.id)
        return {
          ...node,
          data: {
            ...node.data,
            summary: summarizeStage(node.id, data),
            slr: data.slr,
            active: idx <= activeIndex,
            selected: selectedId === node.id,
            dimmed: Boolean(selectedId && selectedId !== node.id),
            justActivated: justActivated === node.id,
          },
        }
      })
    )
  }, [activeIndex, selectedId, justActivated, data, setNodes])

  useEffect(() => {
    setActiveIndex(-1)
    let step = 0
    const timer = setInterval(() => {
      setActiveIndex(step)
      const id = STAGE_ORDER[step]
      setJustActivated(id)
      setTimeout(() => setJustActivated(null), 800)
      step++
      if (step > STAGE_ORDER.length - 1) clearInterval(timer)
    }, 520)
    return () => clearInterval(timer)
  }, [runSignal])

  useEffect(() => {
    if (!pipelineInspectorSignal) return
    setIsPipelineInspectorOpen(true)
  }, [pipelineInspectorSignal])

  useEffect(() => {
    setEdges(
      EDGE_CHAIN.map(([source, target], i) => {
        const src = getStageById(source)
        const isActive = i <= activeIndex
        const isHov = hoveredNodeId === source || hoveredNodeId === target
        const isSelEdge = selectedId === source || selectedId === target
        const isDimmed = Boolean(selectedId && !isSelEdge)
        const stroke = isHov || isSelEdge ? src.accent : isActive ? '#94a3b8' : '#d1d9e4'
        return {
          id: `${source}-${target}`, source, target, type: 'smoothstep',
          markerEnd: { type: MarkerType.ArrowClosed, color: stroke, width: 14, height: 14 },
          animated: isSelEdge || isActive,
          style: { stroke, strokeWidth: isSelEdge || isHov ? 2.8 : isActive ? 1.8 : 1.4, opacity: isDimmed ? 0.08 : isSelEdge ? 1 : isActive ? 0.8 : 0.28, transition: 'all 0.25s ease' },
        }
      })
    )
  }, [activeIndex, hoveredNodeId, selectedId, setEdges])

  // Real screen-space position via viewport transform
  const handleNodeClick = useCallback((e, node) => {
    const stage = getStageById(node.id)
    const { x: vpX, y: vpY, zoom } = getViewport()
    const rect = containerRef.current?.getBoundingClientRect() ?? { left: 0, top: 0 }
    const screenX = rect.left + stage.x * zoom + vpX + (stage.width * zoom) / 2
    const screenY = rect.top + stage.y * zoom + vpY + (stage.height * zoom) / 2
    setInspector({ id: node.id, screenX, screenY, nodeW: stage.width * zoom, nodeH: stage.height * zoom })
    setTab('overview')
  }, [getViewport])

  const sections = buildPipelineSections(data)

  const activeStageName = activeIndex >= 0 && activeIndex < STAGES.length ? STAGES[activeIndex].title : null

  return (
    <section style={{ position: 'relative', borderTop: '1px solid #e8edf3', background: '#f8fafc', flex: '1 1 auto', minHeight: 0, overflow: 'hidden' }}>
      <div style={{ pointerEvents: 'none', position: 'absolute', inset: 0, overflow: 'hidden', zIndex: 0 }}>
        {[{ left: '12%', top: '20%', c: 'rgba(59,130,246,0.05)' }, { left: '42%', top: '15%', c: 'rgba(16,185,129,0.045)' }, { right: '6%', top: '20%', c: 'rgba(99,102,241,0.05)' }].map((b, i) => (
          <div key={i} style={{ position: 'absolute', left: b.left, right: b.right, top: b.top, width: 360, height: 360, borderRadius: '50%', background: `radial-gradient(circle, ${b.c} 0%, transparent 70%)` }} />
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeStageName && (
          <motion.div key={activeStageName}
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }} transition={{ duration: 0.22 }}
            style={{ position: 'absolute', top: 14, left: '50%', transform: 'translateX(-50%)', zIndex: 10, background: 'rgba(255,255,255,0.94)', backdropFilter: 'blur(10px)', border: '1px solid #e2e8f0', borderRadius: 20, padding: '5px 18px', fontSize: 11.5, color: '#64748b', fontWeight: 500, whiteSpace: 'nowrap', boxShadow: '0 2px 12px rgba(15,23,42,0.08)' }}>
            Processing&nbsp;<span style={{ color: '#1e293b', fontWeight: 650 }}>{activeStageName}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ position: 'absolute', bottom: 18, left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: 7, zIndex: 10, alignItems: 'center' }}>
        {STAGES.map((s, i) => (
          <motion.div key={s.id}
            animate={{ background: i <= activeIndex ? s.accent : '#dde3ec', scale: i === activeIndex ? 1.5 : 1, width: i === activeIndex ? 20 : 7 }}
            transition={{ duration: 0.28 }}
            style={{ height: 7, borderRadius: 10, flexShrink: 0 }}
          />
        ))}
      </div>

      <div ref={containerRef} style={{ height: '100%', width: '100%', position: 'relative', zIndex: 1 }}>
        <ReactFlow
          nodes={nodes} edges={edges} nodeTypes={nodeTypes}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onPaneClick={() => setInspector(null)}
          onNodeMouseEnter={(_, n) => setHoveredNodeId(n.id)}
          onNodeMouseLeave={() => setHoveredNodeId(null)}
          fitView fitViewOptions={{ padding: 0.05, minZoom: 0.7, maxZoom: 1.1 }}
          minZoom={0.7} maxZoom={1.5}
          nodesDraggable nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
          style={{ background: 'transparent' }}
        >
          <Background color="#e2e8f0" gap={28} size={1} />
        </ReactFlow>
      </div>

      <PhaseInspector
        open={Boolean(inspector)}
        phaseTitle={selectedId ? getStageById(selectedId)?.title || '' : ''}
        stageAccent={selectedId ? getStageById(selectedId)?.accent : '#6366f1'}
        activeTab={tab}
        onTabChange={setTab}
        onClose={() => setInspector(null)}
        sections={selectedId ? sections[selectedId] : {}}
        nodeScreenX={inspector?.screenX}
        nodeScreenY={inspector?.screenY}
        nodeW={inspector?.nodeW}
        nodeH={inspector?.nodeH}
        stageTitle={selectedId ? getStageById(selectedId)?.title || '' : ''}
        stageAccentBg={selectedId ? getStageById(selectedId)?.accentBg : '#eef2ff'}
        stageGlow={selectedId ? getStageById(selectedId)?.accentGlow : 'rgba(99,102,241,0.2)'}
        stageSummary={selectedId ? summarizeStage(selectedId, data) : ''}
      />

      <PipelineInspectorModal
        open={isPipelineInspectorOpen}
        phases={PIPELINE_PHASES}
        activePhaseId={activePipelinePhaseId}
        onPhaseChange={setActivePipelinePhaseId}
        onClose={() => setIsPipelineInspectorOpen(false)}
        sections={sections}
      />
    </section>
  )
}

export function FlowCanvas({ data, runSignal, pipelineInspectorSignal }) {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner
        data={data}
        runSignal={runSignal}
        pipelineInspectorSignal={pipelineInspectorSignal}
      />
    </ReactFlowProvider>
  )
}
