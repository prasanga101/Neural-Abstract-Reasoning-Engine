import { useEffect, useMemo, useState } from 'react'
import { Background, MarkerType, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { PhaseInspectorModal } from '../canvas/PhaseInspectorModal'

const STAGES = [
  { id: 'input', title: 'Emergency Input', x: 0, stat: 'chunks: 3' },
  { id: 'router', title: 'Router', x: 250, stat: 'top: Evacuation' },
  { id: 'planner', title: 'Planner', x: 500, stat: 'top: Flood Depth' },
  { id: 'slr', title: 'SLR Graph', x: 800, stat: 'nodes: 6, edges: 6' },
  { id: 'executor', title: 'Executor', x: 1100, stat: 'steps: 5' },
  { id: 'verifier', title: 'Verifier', x: 1400, stat: 'valid: pass' },
  { id: 'final', title: 'Final State', x: 1700, stat: 'routes: 3' },
]

const CHAIN = [
  ['input', 'router'],
  ['router', 'planner'],
  ['planner', 'slr'],
  ['slr', 'executor'],
  ['executor', 'verifier'],
  ['verifier', 'final'],
]

const sections = {
  input: {
    overview: <p>Emergency text context and extracted semantic chunks.</p>,
    details: <p>Input is encoded into structured disaster context fields.</p>,
    math: <p>Math / Internals placeholder: text encoding and chunk scoring.</p>,
  },
  router: {
    overview: <p>Router prioritizes operational task intents from context.</p>,
    details: <p>Top task receives highest route confidence score.</p>,
    math: <p>Math / Internals placeholder: thresholding and top-k selection.</p>,
  },
  planner: {
    overview: <p>Planner ranks decision nodes for execution order.</p>,
    details: <p>Nodes are selected by utility score and constraints.</p>,
    math: <p>Math / Internals placeholder: node score optimization.</p>,
  },
  slr: {
    overview: <p>SLR graph resolves dependencies and execution order.</p>,
    details: <p>Directed graph drives dependency-safe task execution.</p>,
    math: <p>Math / Internals placeholder: topological sort and validity checks.</p>,
  },
  executor: {
    overview: <p>Executor runs step sequence from the active plan.</p>,
    details: <p>Tracks completed / skipped / failed execution states.</p>,
    math: <p>Math / Internals placeholder: step transition model.</p>,
  },
  verifier: {
    overview: <p>Verifier checks policy and model-level consistency.</p>,
    details: <p>Combines rule checks with model validation reasoning.</p>,
    math: <p>Math / Internals placeholder: final validity composition.</p>,
  },
  final: {
    overview: <p>Final state summarizes hospitals, routes, and dispatch outputs.</p>,
    details: <p>State artifact is ready for operational decision support.</p>,
    math: <p>Math / Internals placeholder: aggregate state derivation.</p>,
  },
}

function stageLabel(title, stat, isSlr) {
  return (
    <div className="text-left">
      <p className="text-[10px] uppercase tracking-[0.08em] text-slate-400">{title}</p>
      <p className="text-xs text-slate-600">{stat}</p>
      {isSlr ? (
        <div className="mt-2 rounded-md border border-violet-100 bg-violet-50/55 px-2 py-1 text-[10px] text-violet-700">
          dependency core
        </div>
      ) : null}
    </div>
  )
}

export function ReasoningGraphCanvas() {
  const [activeIndex, setActiveIndex] = useState(-1)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    let step = 0
    const timer = setInterval(() => {
      setActiveIndex(step)
      step += 1
      if (step > STAGES.length - 1) clearInterval(timer)
    }, 500)
    return () => clearInterval(timer)
  }, [])

  const nodes = useMemo(
    () =>
      STAGES.map((stage, index) => {
        const isSlr = stage.id === 'slr'
        const isActive = index <= activeIndex
        return {
          id: stage.id,
          position: { x: stage.x, y: 220 },
          data: { label: stageLabel(stage.title, stage.stat, isSlr) },
          draggable: false,
          selectable: false,
          style: {
            width: isSlr ? 280 : 180,
            height: isSlr ? 130 : 86,
            borderRadius: 16,
            border: `1px solid ${selectedNode === stage.id ? '#60a5fa' : '#e2e8f0'}`,
            background: '#ffffff',
            boxShadow:
              selectedNode === stage.id
                ? '0 0 0 2px rgba(191, 219, 254, 0.8), 0 10px 20px rgba(15, 23, 42, 0.08)'
                : '0 8px 18px rgba(15, 23, 42, 0.08)',
            opacity: isActive ? 1 : 0.25,
            transition: 'opacity 240ms ease',
            padding: '8px 10px',
          },
        }
      }),
    [activeIndex, selectedNode]
  )

  const edges = useMemo(
    () =>
      CHAIN.map(([source, target], index) => {
        const isActive = index <= activeIndex
        const isHovered =
          hoveredNode && (hoveredNode === source || hoveredNode === target)
        return {
          id: `${source}-${target}`,
          source,
          target,
          type: 'bezier',
          animated: isActive,
          markerEnd: { type: MarkerType.ArrowClosed, color: '#93a3bf' },
          style: {
            stroke: isHovered ? '#2563eb' : '#93a3bf',
            strokeWidth: isHovered ? 2.8 : 1.9,
            opacity: isActive ? 1 : 0.28,
          },
        }
      }),
    [activeIndex, hoveredNode]
  )

  return (
    <section className="relative border-t border-slate-200 bg-white">
      <div className="h-[620px] w-full bg-white">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={(_, node) => {
            setSelectedNode(node.id)
            setActiveTab('overview')
          }}
          onNodeMouseEnter={(_, node) => setHoveredNode(node.id)}
          onNodeMouseLeave={() => setHoveredNode(null)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.35}
          maxZoom={1.2}
          nodesDraggable={false}
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#e2e8f0" gap={24} />
        </ReactFlow>
      </div>

      <PhaseInspectorModal
        open={Boolean(selectedNode)}
        phaseTitle={selectedNode ? STAGES.find((stage) => stage.id === selectedNode)?.title || '' : ''}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onClose={() => setSelectedNode(null)}
        sections={selectedNode ? sections[selectedNode] : {}}
      />
    </section>
  )
}