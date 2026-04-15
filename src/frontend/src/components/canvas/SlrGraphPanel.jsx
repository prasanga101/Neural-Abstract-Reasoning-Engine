import { useMemo, useState } from 'react'
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

function getNodeColor(role) {
  if (role === 'router') return '#dbeafe'
  if (role === 'planner') return '#dcfce7'
  if (role === 'executor') return '#fef3c7'
  if (role === 'verifier') return '#fce7f3'
  if (role === 'state') return '#ede9fe'
  return '#e0e7ff'
}

export function SlrGraphPanel({ slr }) {
  const [selectedNode, setSelectedNode] = useState(null)

  const nodes = useMemo(() => {
    return slr.nodes.map((node, index) => ({
      id: node.id,
      data: { label: node.label },
      position: {
        x: 50 + index * 130,
        y: index % 2 === 0 ? 40 : 170,
      },
      style: {
        borderRadius: 10,
        border: '1px solid #cbd5e1',
        background: getNodeColor(node.role),
        fontSize: 12,
        padding: '6px 8px',
      },
    }))
  }, [slr.nodes])

  const edges = useMemo(() => {
    return slr.edges.map((edge, index) => ({
      id: `${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b' },
      style: { stroke: '#94a3b8', strokeWidth: 1.4 },
    }))
  }, [slr.edges])

  return (
    <div className="space-y-2.5">
      <div className="h-[270px] overflow-hidden rounded-2xl border border-violet-100/80 bg-white/75">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={(_, node) => setSelectedNode(node.id)}
          nodesDraggable
          nodesConnectable={false}
          panOnDrag
          zoomOnPinch
        >
          <Background color="#e2e8f0" gap={26} />
          <MiniMap zoomable pannable />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <div className="rounded-xl border border-violet-100/70 bg-white/70 px-2.5 py-1.5 text-[11px]">
        {selectedNode ? (
          <p className="text-slate-700">
            Inspecting node: <span className="font-semibold">{selectedNode}</span>{' '}
            | dependencies resolved in ordered execution.
          </p>
        ) : (
          <p className="text-slate-500">
            Click a graph node to inspect its role and dependency context.
          </p>
        )}
      </div>
    </div>
  )
}
