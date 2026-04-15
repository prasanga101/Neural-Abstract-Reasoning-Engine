import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  MarkerType,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
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

const STAGE_STYLE = {
  input: { accent: '#06b6d4', icon: 'IN' },
  router: { accent: '#3b82f6', icon: 'RT' },
  planner: { accent: '#10b981', icon: 'PL' },
  slr: { accent: '#8b5cf6', icon: 'SG' },
  executor: { accent: '#f59e0b', icon: 'EX' },
  verifier: { accent: '#ec4899', icon: 'VF' },
  final: { accent: '#6366f1', icon: 'FS' },
}

function StageNode({ data, selected }) {
  const accent = STAGE_STYLE[data.id].accent
  const isSlr = data.id === 'slr'
  return (
    <div
      style={{
        borderRadius: 20,
        border: `1px solid ${selected ? accent : '#e2e8f0'}`,
        borderTop: `3px solid ${accent}`,
        background: '#ffffff',
        boxShadow: selected
          ? `0 0 0 2px ${accent}22, 0 18px 30px rgba(15, 23, 42, 0.12)`
          : data.active
            ? `0 10px 24px rgba(15, 23, 42, 0.09), 0 0 0 1px ${accent}22`
            : '0 8px 18px rgba(15, 23, 42, 0.07)',
        opacity: data.active ? 1 : 0.35,
        padding: isSlr ? '14px 14px' : '12px 12px',
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        transition: 'all 220ms ease',
      }}
    >
      <div className="mb-2 flex items-center gap-2">
        <span
          className="inline-flex h-6 w-6 items-center justify-center rounded-lg text-[10px] font-semibold text-white shadow-sm"
          style={{ background: `linear-gradient(135deg, ${accent}, #1f2937)` }}
        >
          {STAGE_STYLE[data.id].icon}
        </span>
        <p className="text-[11px] font-semibold tracking-[0.02em] text-slate-800">
          {data.title}
        </p>
      </div>
      <p className="text-[11px] text-slate-500">{data.stat}</p>
      {isSlr ? (
        <div className="mt-2 rounded-lg border border-violet-100 bg-violet-50/60 px-2 py-1 text-[10px] font-medium text-violet-700">
          dependency core
        </div>
      ) : null}
    </div>
  )
}

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

export function ReasoningGraphCanvas() {
  const [activeIndex, setActiveIndex] = useState(-1)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [nodes, setNodes, onNodesChange] = useNodesState(
    STAGES.map((stage) => ({
      id: stage.id,
      type: 'stageNode',
      position: { x: stage.x, y: 220 },
      data: { id: stage.id, title: stage.title, stat: stage.stat, active: false },
      draggable: true,
      selectable: true,
      style: { width: stage.id === 'slr' ? 360 : 210, height: stage.id === 'slr' ? 170 : 104 },
    }))
  )
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const nodeTypes = useMemo(() => ({ stageNode: StageNode }), [])

  useEffect(() => {
    let step = 0
    const timer = setInterval(() => {
      setActiveIndex(step)
      step += 1
      if (step > STAGES.length - 1) clearInterval(timer)
    }, 500)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    setNodes((current) =>
      current.map((node) => {
        const stageIndex = STAGES.findIndex((item) => item.id === node.id)
        const isActive = stageIndex <= activeIndex
        const isSelected = selectedNode === node.id
        const isHovered = hoveredNode === node.id

        return {
          ...node,
          data: {
            ...node.data,
            active: isActive,
          },
          style: {
            ...node.style,
            transform: isHovered ? 'translateY(-1px)' : 'translateY(0)',
            transition: 'all 220ms ease',
          },
          selected: isSelected,
        }
      })
    )
  }, [activeIndex, hoveredNode, selectedNode, setNodes])

  useEffect(() => {
    const nextEdges = CHAIN.map(([source, target], index) => {
      const isActive = index <= activeIndex
      const isHovered =
        hoveredNode && (hoveredNode === source || hoveredNode === target)
      return {
        id: `${source}-${target}`,
        source,
        target,
        type: 'bezier',
        animated: isActive,
        markerEnd: { type: MarkerType.ArrowClosed, color: isHovered ? '#2563eb' : '#8aa0c2' },
        style: {
          stroke: isHovered ? '#2563eb' : '#8aa0c2',
          strokeWidth: isHovered ? 3 : 2,
          opacity: isActive ? 0.96 : 0.24,
          filter: isHovered ? 'drop-shadow(0 0 4px rgba(59,130,246,0.35))' : 'none',
        },
      }
    })
    setEdges(nextEdges)
  }, [activeIndex, hoveredNode, setEdges])

  return (
    <section className="relative border-t border-slate-200 bg-white">
      <div className="h-[620px] w-full bg-white">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => {
            setSelectedNode(node.id)
            setActiveTab('overview')
          }}
          onNodeMouseEnter={(_, node) => setHoveredNode(node.id)}
          onNodeMouseLeave={() => setHoveredNode(null)}
          defaultViewport={{ x: -120, y: 20, zoom: 0.62 }}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.35}
          maxZoom={1.2}
          nodesDraggable
          nodeDragThreshold={1}
          nodesConnectable={false}
          panOnDrag={[1, 2]}
          defaultEdgeOptions={{ type: 'bezier' }}
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
