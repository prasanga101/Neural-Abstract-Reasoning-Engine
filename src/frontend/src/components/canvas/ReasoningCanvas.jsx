import { useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { DraggablePhasePanel } from './DraggablePhasePanel'
import { EmergencyContextPanel } from './EmergencyContextPanel'
import { RouterPanel } from './RouterPanel'
import { PlannerPanel } from './PlannerPanel'
import { SlrGraphPanel } from './SlrGraphPanel'
import { ExecutorPanel } from './ExecutorPanel'
import { VerifierPanel } from './VerifierPanel'
import { FinalStatePanel } from './FinalStatePanel'
import { PhaseInspectorModal } from './PhaseInspectorModal'

const phaseOrder = ['input', 'router', 'planner', 'slr', 'executor', 'verifier', 'final']

function formatRoute(route) {
  const distanceKm =
    typeof route?.distance_km === 'number'
      ? route.distance_km
      : typeof route?.distance_m === 'number'
        ? route.distance_m / 1000
        : typeof route?.distance === 'number'
          ? route.distance / 1000
          : null
  const durationMin =
    typeof route?.duration_min === 'number'
      ? route.duration_min
      : typeof route?.duration_s === 'number'
        ? route.duration_s / 60
        : typeof route?.duration === 'number'
          ? route.duration / 60
          : null

  if (distanceKm == null || durationMin == null) return null
  return `${distanceKm.toFixed(2)} km / ${durationMin.toFixed(1)} min`
}

function DetailList({ items }) {
  return (
    <ul className="space-y-1">
      {items.filter(Boolean).map((item) => (
        <li key={item} className="rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-700">
          {item}
        </li>
      ))}
    </ul>
  )
}

export function ReasoningCanvas({ data }) {
  const dragConstraintsRef = useRef(null)
  const [hoveredPhase, setHoveredPhase] = useState(null)
  const [playhead, setPlayhead] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [inspector, setInspector] = useState(null)

  useEffect(() => {
    if (!isPlaying) return undefined
    const timer = setInterval(() => {
      setPlayhead((current) => {
        if (current >= phaseOrder.length - 1) {
          setIsPlaying(false)
          return current
        }
        return current + 1
      })
    }, 900)
    return () => clearInterval(timer)
  }, [isPlaying])

  const flowLinks = useMemo(
    () => [
      { id: 'input-router', from: 'input', top: '28%', left: '11%', width: '10%' },
      { id: 'router-planner', from: 'router', top: '31%', left: '24%', width: '9%' },
      { id: 'planner-slr', from: 'planner', top: '34%', left: '37%', width: '10%' },
      { id: 'slr-executor', from: 'slr', top: '40%', left: '61%', width: '8%' },
      { id: 'executor-verifier', from: 'executor', top: '46%', left: '75%', width: '6%' },
      { id: 'verifier-final', from: 'verifier', top: '52%', left: '84%', width: '6%' },
    ],
    []
  )

  const inspectorMap = useMemo(
    () => {
      const populationDemands = data.state.population_demands
      const affectedPopulation =
        data.state.estimated_affected_population ??
        populationDemands?.estimated_affected_population
      const populationDetail = populationDemands
        ? `raster population: ${
            affectedPopulation?.toLocaleString() ?? 'unknown'
          } affected / ${populationDemands.demand_level ?? 'unknown'} demand / source: ${
            populationDemands.source ?? 'unknown'
          }`
        : 'raster population: not available'
      const bestRoute = data.state.best_route
      const bestRouteStats = formatRoute(bestRoute)
      const bestRouteDetail =
        bestRouteStats
          ? `best route: ${bestRoute.hospital ?? 'selected hospital'} / ${bestRouteStats}`
          : 'best route: not available'
      const blockedRoutes = data.state.blocked_routes.filter(Boolean)
      const blockedRoutesDetail = blockedRoutes.length
        ? `blocked routes: ${blockedRoutes.join(', ')}`
        : 'blocked routes: No routes are blocked'

      return ({
      input: {
        title: 'Emergency Input Context',
        sections: {
          overview: (
            <p>
              Raw emergency text is chunked into context units to seed downstream reasoning
              stages.
            </p>
          ),
          details: <DetailList items={data.message.split(/[,.]/).filter(Boolean)} />,
          math: (
            <div className="space-y-2">
              <p>Message is split into emergency facts, preserving location, casualty, shelter, and routing signals for downstream stages.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'chunks = split(message, /[,.!?]/)\ncontext = normalize(location + urgency + needs)\nstate_0 = { message, context }'}
              </code>
            </div>
          ),
        },
      },
      router: {
        title: 'Router',
        sections: {
          overview: <p>Router selects operational tasks from encoded context.</p>,
          details: (
            <DetailList
              items={data.router.scores.map(
                (row) => `${row.task}: ${(row.score * 100).toFixed(1)}%`
              )}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>Task routing combines classifier scores with emergency keywords so medical, shelter, and route work cannot be dropped from a mixed incident.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'scores = classifier(context)\ntasks = { t | score(t) >= threshold }\nif medical_terms: tasks += hospital + ambulance\nif shelter_terms: tasks += shelter_allocation\nif route_terms: tasks += route_planning'}
              </code>
            </div>
          ),
        },
      },
      planner: {
        title: 'Planner',
        sections: {
          overview: <p>Planner prioritizes reasoning nodes for execution ordering.</p>,
          details: (
            <DetailList
              items={data.planner.scores.map(
                (row) => `${row.node}: ${(row.score * 100).toFixed(1)}%`
              )}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>Planner expands routed tasks into executable nodes, then orders high-risk operations before reporting and verification.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'nodes = expand(tasks)\npriority(node) = severity_weight + dependency_weight\nplan = sort(nodes, priority desc)'}
              </code>
            </div>
          ),
        },
      },
      slr: {
        title: 'SLR Graph',
        sections: {
          overview: <p>Dependency graph resolves stage order and execution compatibility.</p>,
          details: (
            <DetailList
              items={data.slr.order.map(
                (nodeId, index) => `#${index + 1} execution slot -> ${nodeId}`
              )}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>
                SLR builds a dependency graph so route scans, hospital lookup, ambulance
                dispatch, and shelter allocation run in a valid order.
              </p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'G = (V, E)\nE includes: collect_sensor_data -> identify_alternative_routes\nE includes: identify_nearest_hospitals -> dispatch_ambulances\norder = topological_sort(G)'}
              </code>
            </div>
          ),
        },
      },
      executor: {
        title: 'Executor',
        sections: {
          overview: <p>Executor applies the plan and tracks each operational step.</p>,
          details: (
            <DetailList
              items={data.executor.timeline.map(
                (item) => `Step ${item.step}: ${item.node} (${item.status})`
              )}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>Executor applies each tool result to the tracked emergency state and records completed, skipped, or failed steps in the timeline.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'for node in order:\n  result = run_tool(node, state_t)\n  state_t+1 = merge(state_t, result.updates)\n  timeline += { node, status, result }'}
              </code>
            </div>
          ),
        },
      },
      verifier: {
        title: 'Verifier',
        sections: {
          overview: <p>Verifier validates safety rules and model-level consistency.</p>,
          details: (
            <DetailList
              items={[
                `valid: ${String(data.verifier.valid)}`,
                `rule: ${String(data.verifier.rule)}`,
                `gemini: ${String(data.verifier.gemini)}`,
                data.verifier.reason,
              ]}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>Verifier fuses deterministic safety rules with the local Ollama model check; depleted but nonnegative resources are allowed after dispatch.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {'rule_ok = ambulances >= 0 AND shelters >= 0\nmodel_ok = ollama_validate(trace, final_state)\nvalid = rule_ok AND model_ok'}
              </code>
            </div>
          ),
        },
      },
      final: {
        title: 'Final State',
        sections: {
          overview: <p>Derived response state is emitted for operators and routing systems.</p>,
          details: (
            <DetailList
              items={[
                `ambulances: ${data.state.ambulances}`,
                `shelters: ${data.state.shelters}`,
                populationDetail,
                blockedRoutesDetail,
                bestRouteDetail,
              ]}
            />
          ),
          math: (
            <div className="space-y-2">
              <p>Final state is derived from real tool outputs: nearby hospital candidates, Dijkstra/OSRM route costs, blocked-route scan results, and resource allocation counts.</p>
              <code className="block rounded bg-slate-100 p-2 text-xs">
                {`hospitals = nearest(event_coordinates, hospital_index)\nblocked_edges = scan_roads(event_coordinates)\nif blocked_edges is empty: blocked_routes = []\nbest_route = min(Dijkstra(graph, event, hospital) for hospital in hospitals)\nstate* = { hospitals, best_route, blocked_routes, ambulances, shelters }\n${bestRouteDetail}`}
              </code>
            </div>
          ),
        },
      },
    })},
    [data]
  )

  const openInspector = (phase) => {
    setInspector(phase)
    setActiveTab('overview')
  }

  return (
    <section className="border-t border-slate-200/70 bg-white/90">
      <div className="flex items-center justify-between px-4 py-2.5">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-slate-900">
            NARE Interactive Reasoning Canvas
          </h2>
          <p className="text-[11px] text-slate-500">
            Drag phases, inspect internals, and replay left-to-right reasoning.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-full border border-slate-300/80 bg-white px-3 py-1 text-[11px] text-slate-700 hover:bg-slate-50"
            onClick={() => {
              setPlayhead(0)
              setIsPlaying(true)
            }}
          >
            Replay
          </button>
          <button
            type="button"
            className="rounded-full border border-blue-300/80 bg-blue-50/70 px-3 py-1 text-[11px] text-blue-700 hover:bg-blue-100/70"
            onClick={() => setIsPlaying((value) => !value)}
          >
            {isPlaying ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      <div className="overflow-x-auto border-t border-slate-100">
        <div
          ref={dragConstraintsRef}
          className="relative h-[640px] min-w-[1680px] bg-gradient-to-b from-white via-slate-50/30 to-slate-50/70"
        >
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-[8%] top-[30%] h-56 w-56 rounded-full bg-cyan-100/40 blur-3xl" />
            <div className="absolute left-[42%] top-[18%] h-72 w-72 rounded-full bg-blue-100/40 blur-3xl" />
            <div className="absolute right-[6%] top-[34%] h-64 w-64 rounded-full bg-violet-100/45 blur-3xl" />
          </div>

          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox="0 0 1680 640"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="nareFlowBlue" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#bfdbfe" stopOpacity="0.55" />
                <stop offset="45%" stopColor="#93c5fd" stopOpacity="0.45" />
                <stop offset="100%" stopColor="#c4b5fd" stopOpacity="0.48" />
              </linearGradient>
              <linearGradient id="nareFlowSoft" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#bae6fd" stopOpacity="0.42" />
                <stop offset="100%" stopColor="#ddd6fe" stopOpacity="0.4" />
              </linearGradient>
            </defs>
            <path
              d="M120 240 C 280 210, 420 215, 580 260 C 760 310, 930 320, 1120 292 C 1310 262, 1450 288, 1610 322"
              fill="none"
              stroke="url(#nareFlowBlue)"
              strokeWidth="28"
              strokeLinecap="round"
            />
            <path
              d="M128 292 C 300 268, 460 284, 620 330 C 780 374, 930 390, 1115 364 C 1280 340, 1430 352, 1600 380"
              fill="none"
              stroke="url(#nareFlowSoft)"
              strokeWidth="18"
              strokeLinecap="round"
            />
          </svg>

          <div className="pointer-events-none absolute left-[34px] top-6 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400">
            Emergency Input
          </div>
          <div className="pointer-events-none absolute left-[302px] top-8 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400">
            Router
          </div>
          <div className="pointer-events-none absolute left-[560px] top-8 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400">
            Planner
          </div>
          <div className="pointer-events-none absolute left-[782px] top-10 text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">
            SLR Reasoning Graph
          </div>
          <div className="pointer-events-none absolute left-[1300px] top-8 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400">
            Executor + Verifier
          </div>
          <div className="pointer-events-none absolute left-[1548px] top-8 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-400">
            Final State
          </div>

          {flowLinks.map((link) => {
            const highlighted = hoveredPhase === link.from
            return (
              <motion.div
                key={link.id}
                className="absolute h-[2px] rounded-full bg-gradient-to-r from-blue-200 via-blue-500 to-violet-300"
                style={{ top: link.top, left: link.left, width: link.width }}
                animate={{ opacity: highlighted ? 0.9 : 0.2 }}
              />
            )
          })}

          <DraggablePhasePanel
            id="input"
            title="Emergency Input Context"
            subtitle="Encoded signal intake"
            initialPosition={{ x: 18, y: 92 }}
            stageIndex={0}
            visible={playhead >= 0}
            isHighlighted={hoveredPhase === 'input'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('input')}
            className="w-[230px]"
            tone="cyan"
          >
            <EmergencyContextPanel message={data.message} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="router"
            title="Router"
            subtitle="Task intent selection"
            initialPosition={{ x: 260, y: 130 }}
            stageIndex={1}
            visible={playhead >= 1}
            isHighlighted={hoveredPhase === 'router'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('router')}
            className="w-[250px]"
            tone="blue"
          >
            <RouterPanel router={data.router} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="planner"
            title="Planner"
            subtitle="Node ranking and plan shaping"
            initialPosition={{ x: 525, y: 150 }}
            stageIndex={2}
            visible={playhead >= 2}
            isHighlighted={hoveredPhase === 'planner'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('planner')}
            className="w-[275px]"
            tone="emerald"
          >
            <PlannerPanel planner={data.planner} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="slr"
            title="SLR Graph"
            subtitle="Dependency graph and execution order"
            initialPosition={{ x: 640, y: 230 }}
            stageIndex={3}
            visible={playhead >= 3}
            isHighlighted={hoveredPhase === 'slr'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('slr')}
            className="w-[620px]"
            tone="violet"
          >
            <SlrGraphPanel slr={data.slr} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="executor"
            title="Executor"
            subtitle="Step-by-step operational playback"
            initialPosition={{ x: 1285, y: 140 }}
            stageIndex={4}
            visible={playhead >= 4}
            isHighlighted={hoveredPhase === 'executor'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('executor')}
            className="w-[230px]"
            tone="blue"
          >
            <ExecutorPanel executor={data.executor} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="verifier"
            title="Verifier"
            subtitle="Rule and model validity checks"
            initialPosition={{ x: 1295, y: 350 }}
            stageIndex={5}
            visible={playhead >= 5}
            isHighlighted={hoveredPhase === 'verifier'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('verifier')}
            className="w-[220px]"
            tone="rose"
          >
            <VerifierPanel verifier={data.verifier} />
          </DraggablePhasePanel>

          <DraggablePhasePanel
            id="final"
            title="Final State"
            subtitle="Output state synthesis"
            initialPosition={{ x: 1530, y: 250 }}
            stageIndex={6}
            visible={playhead >= 6}
            isHighlighted={hoveredPhase === 'final'}
            dragConstraintsRef={dragConstraintsRef}
            onHover={setHoveredPhase}
            onOpen={() => openInspector('final')}
            className="w-[220px]"
            tone="violet"
          >
            <FinalStatePanel state={data.state} />
          </DraggablePhasePanel>
        </div>
      </div>

      <PhaseInspectorModal
        open={Boolean(inspector)}
        phaseTitle={inspector ? inspectorMap[inspector].title : ''}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onClose={() => setInspector(null)}
        sections={inspector ? inspectorMap[inspector].sections : {}}
      />
    </section>
  )
}
