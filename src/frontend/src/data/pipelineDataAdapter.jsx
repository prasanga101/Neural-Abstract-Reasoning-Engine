const EMPTY_PIPELINE_DATA = {
  message: '',
  router: {
    tasks: [],
    scores: [],
    top: null,
    rl: {
      action: null,
      injected: false,
      source: null,
      classifier_tasks: [],
    },
  },
  planner: {
    nodes: [],
    scores: [],
    top: null,
  },
  slr: {
    nodes: [],
    edges: [],
    order: [],
  },
  executor: {
    status: 'idle',
    timeline: [],
  },
  verifier: {
    valid: false,
    rule: false,
    gemini: false,
    reason: '',
  },
  state: {
    ambulances: 0,
    shelters: 0,
    hospitals: [],
    blocked_routes: [],
    blocked_route_details: [],
    blocked_route_detection: null,
    routes: [],
    best_route: null,
    routing_graph: null,
    resolved_location: null,
    event_coordinates: null,
    infrastructure_damage: null,
    disaster_zone_scan: null,
    trapped_victims: null,
    rescue_teams_allocated: null,
    hospital_capacity_plan: null,
    resource_allocation_plan: null,
    information_summary: null,
    public_report: null,
    population_demands: null,
    estimated_affected_population: null,
    raster_population: null,
    rasterio_population: null,
    population_summary: null,
  },
}

function asArray(value) {
  return Array.isArray(value) ? value : []
}

function asObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
}

function normalizeSlrNodes(nodes) {
  return asArray(nodes).map((node, index) => {
    if (typeof node === 'string') {
      return {
        id: `slr-${index + 1}`,
        label: node,
        name: node,
      }
    }

    const source = asObject(node)
    const label = source.label ?? source.name ?? source.id ?? `Node ${index + 1}`

    return {
      ...source,
      id: source.id ?? `slr-${index + 1}`,
      label,
      name: source.name ?? label,
    }
  })
}

function normalizeSlrEdges(edges) {
  return asArray(edges).map((edge) => {
    if (Array.isArray(edge) && edge.length >= 2) {
      return { source: edge[0], target: edge[1] }
    }

    const source = asObject(edge)
    return {
      source: source.source ?? null,
      target: source.target ?? null,
    }
  })
}

function roundNumber(value, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) return null
  return Number(value.toFixed(digits))
}

function formatScore(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return null
  return value <= 1 ? `${Math.round(value * 100)}%` : `${roundNumber(value)}`
}

function formatRoute(route) {
  if (!route || typeof route !== 'object') return null
  const parts = []
  const distanceKm =
    typeof route.distance_km === 'number'
      ? route.distance_km
      : typeof route.distance_m === 'number'
        ? route.distance_m / 1000
        : typeof route.distance === 'number'
          ? route.distance / 1000
          : null
  const durationMin =
    typeof route.duration_min === 'number'
      ? route.duration_min
      : typeof route.duration_s === 'number'
        ? route.duration_s / 60
        : typeof route.duration === 'number'
          ? route.duration / 60
          : null

  if (typeof distanceKm === 'number') parts.push(`${roundNumber(distanceKm, 2)} km`)
  if (typeof durationMin === 'number') parts.push(`${roundNumber(durationMin, 1)} min`)
  return parts.join(' · ')
}

function quotedList(items) {
  const values = asArray(items).filter(Boolean)
  if (!values.length) return ''
  return values.map((value) => `"${value}"`).join(', ')
}

function hasKeywordMatch(values, keywords) {
  const haystack = asArray(values)
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())

  return haystack.some((value) => keywords.some((keyword) => value.includes(keyword)))
}

function chunkCount(message) {
  const text = typeof message === 'string' ? message : ''
  return text.split(/[,.!?]/).map((part) => part.trim()).filter(Boolean).length
}

function JsonBlock({ value }) {
  return (
    <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, margin: 0 }}>
      {JSON.stringify(value, null, 2)}
    </pre>
  )
}

function BulletSummary({ items }) {
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {items.map((item) => (
        <div key={item.label}>
          <p style={{ margin: 0, fontSize: 12, fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase', color: '#94a3b8' }}>
            {item.label}
          </p>
          <p style={{ margin: '4px 0 0', color: '#334155' }}>{item.value}</p>
        </div>
      ))}
    </div>
  )
}

function ExecutionOrder({ title = 'Execution Order', steps = [] }) {
  const visibleSteps = asArray(steps).filter(Boolean)
  if (!visibleSteps.length) return null

  return (
    <div
      style={{
        marginTop: 14,
        border: '1px solid #e2e8f0',
        borderRadius: 14,
        background: 'linear-gradient(180deg, #ffffff, #f8fafc)',
        padding: 12,
      }}
    >
      <p
        style={{
          margin: 0,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#94a3b8',
        }}
      >
        {title}
      </p>
      <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
        <div
          style={{
            display: 'grid',
            gap: 8,
            maxHeight: 248,
            overflowY: 'auto',
            paddingRight: 4,
          }}
        >
          {visibleSteps.map((step, index) => (
            <div
              key={`${title}-${step}-${index}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  flexShrink: 0,
                  borderRadius: 999,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#e2e8f0',
                  color: '#334155',
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                {index + 1}
              </div>
              <div
                style={{
                  borderRadius: 10,
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  padding: '8px 10px',
                  color: '#334155',
                  fontSize: 13,
                  lineHeight: 1.5,
                  width: '100%',
                }}
              >
                {step}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FormulaFlow({
  title,
  equation,
  steps = [],
  metrics = [],
  accent = '#6366f1',
}) {
  return (
    <div className="formula-flow" style={{ '--formula-accent': accent }}>
      <div className="formula-flow__header">
        <span className="formula-flow__pulse" />
        <p>{title}</p>
      </div>

      <div className="formula-flow__equation">
        {equation}
      </div>

      <div className="formula-flow__steps">
        {steps.map((step, index) => (
          <div
            className="formula-flow__step"
            key={`${title}-${step.label}-${index}`}
            style={{ animationDelay: `${index * 120}ms` }}
          >
            <span className="formula-flow__index">{index + 1}</span>
            <div>
              <p>{step.label}</p>
              <span>{step.value}</span>
            </div>
          </div>
        ))}
      </div>

      {metrics.length ? (
        <div className="formula-flow__metrics">
          {metrics.map((metric) => (
            <div className="formula-flow__metric" key={`${title}-${metric.label}`}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function isPipelineVizData(value) {
  const data = asObject(value)
  return Boolean(
    'message' in data &&
      'router' in data &&
      'planner' in data &&
      'slr' in data &&
      'executor' in data &&
      'verifier' in data &&
      'state' in data
  )
}

export function normalizePipelineData(rawData) {
  const data = asObject(rawData)
  const router = asObject(data.router)
  const planner = asObject(data.planner)
  const slr = asObject(data.slr)
  const executor = asObject(data.executor)
  const verifier = asObject(data.verifier)
  const state = asObject(data.state)
  const populationDemands = state.population_demands ? asObject(state.population_demands) : null
  const rasterPopulation = state.raster_population
    ? asObject(state.raster_population)
    : populationDemands
  const rasterioPopulation = state.rasterio_population
    ? asObject(state.rasterio_population)
    : rasterPopulation

  return {
    message: typeof data.message === 'string' ? data.message : EMPTY_PIPELINE_DATA.message,
    router: {
      tasks: asArray(router.tasks),
      scores: asArray(router.scores),
      top: router.top ?? null,
      rl: {
        action: asObject(router.rl).action ?? null,
        injected: Boolean(asObject(router.rl).injected),
        source: asObject(router.rl).source ?? null,
        classifier_tasks: asArray(asObject(router.rl).classifier_tasks),
      },
    },
    planner: {
      nodes: asArray(planner.nodes),
      scores: asArray(planner.scores),
      top: planner.top ?? null,
    },
    slr: {
      nodes: normalizeSlrNodes(slr.nodes),
      edges: normalizeSlrEdges(slr.edges),
      order: asArray(slr.order),
    },
    executor: {
      status: typeof executor.status === 'string' ? executor.status : EMPTY_PIPELINE_DATA.executor.status,
      timeline: asArray(executor.timeline),
    },
    verifier: {
      valid: Boolean(verifier.valid),
      rule: Boolean(verifier.rule),
      gemini: Boolean(verifier.gemini),
      reason: typeof verifier.reason === 'string' ? verifier.reason : '',
    },
    state: {
      ambulances: typeof state.ambulances === 'number' ? state.ambulances : 0,
      shelters: typeof state.shelters === 'number' ? state.shelters : 0,
      hospitals: asArray(state.hospitals),
      blocked_routes: asArray(state.blocked_routes),
      blocked_route_details: asArray(state.blocked_route_details),
      blocked_route_detection: state.blocked_route_detection
        ? asObject(state.blocked_route_detection)
        : null,
      routes: asArray(state.routes),
      best_route: asObject(state.best_route),
      routing_graph: state.routing_graph ? asObject(state.routing_graph) : null,
      resolved_location: state.resolved_location ? asObject(state.resolved_location) : null,
      event_coordinates: state.event_coordinates ? asObject(state.event_coordinates) : null,
      infrastructure_damage: state.infrastructure_damage ? asObject(state.infrastructure_damage) : null,
      disaster_zone_scan: state.disaster_zone_scan ? asObject(state.disaster_zone_scan) : null,
      trapped_victims: state.trapped_victims ? asObject(state.trapped_victims) : null,
      rescue_teams_allocated:
        typeof state.rescue_teams_allocated === 'number' ? state.rescue_teams_allocated : null,
      hospital_capacity_plan: state.hospital_capacity_plan ? asObject(state.hospital_capacity_plan) : null,
      resource_allocation_plan: state.resource_allocation_plan ? asObject(state.resource_allocation_plan) : null,
      information_summary: state.information_summary ? asObject(state.information_summary) : null,
      public_report: state.public_report ? asObject(state.public_report) : null,
      population_demands: populationDemands,
      estimated_affected_population:
        typeof state.estimated_affected_population === 'number'
          ? state.estimated_affected_population
          : null,
      raster_population: rasterPopulation,
      rasterio_population: rasterioPopulation,
      population_summary:
        typeof state.population_summary === 'string' ? state.population_summary : null,
    },
  }
}

export function pipelineDataFromInput(inputText, fallbackData) {
  const text = typeof inputText === 'string' ? inputText.trim() : ''
  const fallback = normalizePipelineData(fallbackData)

  if (!text.startsWith('{')) {
    return {
      data: {
        ...fallback,
        message: inputText,
      },
      source: 'message',
    }
  }

  try {
    const parsed = JSON.parse(text)
    if (!isPipelineVizData(parsed)) {
      return { data: fallback, source: 'invalid-json' }
    }

    return {
      data: normalizePipelineData(parsed),
      source: 'json',
    }
  } catch {
    return { data: fallback, source: 'invalid-json' }
  }
}

export function summarizeStage(id, rawData) {
  const data = normalizePipelineData(rawData)

  if (id === 'input') return `${chunkCount(data.message)} chunks`
  if (id === 'router') return data.router.top ? `top → ${data.router.top}` : `${data.router.tasks.length} tasks`
  if (id === 'planner') return data.planner.top ? `top → ${data.planner.top}` : `${data.planner.nodes.length} nodes`
  if (id === 'slr') return `${data.slr.nodes.length} nodes · ${data.slr.edges.length} edges`
  if (id === 'executor') return `${data.executor.timeline.length} steps`
  if (id === 'verifier') return data.verifier.valid ? 'passed ✓' : 'failed ✗'
  return `${data.state.routes.length} routes`
}

export function buildPipelineSections(rawData) {
  const data = normalizePipelineData(rawData)
  const completedSteps = data.executor.timeline.filter((step) => step.status === 'completed').length
  const skippedSteps = data.executor.timeline.filter((step) => step.status === 'skipped').length
  const failedSteps = data.executor.timeline.filter((step) => step.status === 'failed').length
  const bestRoute = formatRoute(data.state.best_route)
  const bestRouteHospital = data.state.best_route?.hospital
  const topRouterScore = data.router.scores.find((entry) => entry.task === data.router.top)?.score
  const topPlannerScore = data.planner.scores.find((entry) => entry.node === data.planner.top)?.score
  const rasterPopulation = data.state.raster_population ?? data.state.population_demands
  const rasterRadius = rasterPopulation?.radius_km
  const rasterSource = rasterPopulation?.source ?? 'unknown'
  const bestRouteDistance = bestRoute ?? 'no route selected'
  const plannerPreview = quotedList(data.planner.nodes.slice(0, 3))
  const topSlrOrder = quotedList(data.slr.order.slice(0, 4))
  const topHospitals = quotedList(
    data.state.hospitals.map((hospital) => hospital?.name).filter(Boolean).slice(0, 3)
  )
  const topBlockedRoutes = quotedList(data.state.blocked_routes.slice(0, 3))
  const topTasks = quotedList(data.router.tasks.slice(0, 3))
  const topTimelineNodes = quotedList(
    data.executor.timeline.map((step) => step?.node).filter(Boolean).slice(0, 4)
  )
  const rlClassifierTasks = quotedList(data.router.rl.classifier_tasks.slice(0, 3))
  const routerPriorityOrder = data.router.scores.length
    ? data.router.scores.map((entry) => entry.task)
    : data.router.tasks
  const plannerOrder = data.planner.scores.length
    ? data.planner.scores.map((entry) => entry.node)
    : data.planner.nodes
  const slrResolvedOrder = data.slr.order.length
    ? data.slr.order
    : data.slr.nodes.map((node) => node.label ?? node.name ?? node.id)
  const executorOrder = data.executor.timeline.map((step) =>
    `${step.node}${step.status ? ` — ${step.status}` : ''}`
  )
  const taskAndNodeContext = [
    ...data.router.tasks,
    data.router.top,
    ...data.planner.nodes,
    data.planner.top,
    ...data.executor.timeline.map((step) => step?.node),
  ]
  const mentionsMedical = hasKeywordMatch(taskAndNodeContext, [
    'ambulance',
    'hospital',
    'medical',
    'injury',
    'casualt',
    'triage',
  ])
  const mentionsShelter = hasKeywordMatch(taskAndNodeContext, [
    'shelter',
    'evac',
    'displace',
    'relief',
    'allocation',
  ])
  const mentionsRouting = hasKeywordMatch(taskAndNodeContext, [
    'route',
    'transport',
    'corridor',
    'blocked',
    'access',
    'hospital',
  ])
  const finalStateSentences = []

  if (mentionsMedical || data.state.hospitals.length || data.state.ambulances) {
    if (data.state.hospitals.length) {
      finalStateSentences.push(
        `${data.state.hospitals.length} hospital option${
          data.state.hospitals.length === 1 ? '' : 's'
        } were surfaced${topHospitals ? `, including ${topHospitals}` : ''}.`
      )
    } else if (mentionsMedical) {
      finalStateSentences.push(
        `Medical response was part of the request, but no nearby hospital options were returned in the final state.`
      )
    }

    if (mentionsMedical) {
      finalStateSentences.push(
        `${data.state.ambulances} ambulance${
          data.state.ambulances === 1 ? '' : 's'
        } remain available in the tracked state after execution.`
      )
    }
  }

  if (mentionsShelter || data.state.shelters) {
    finalStateSentences.push(
      `${data.state.shelters} shelter${
        data.state.shelters === 1 ? '' : 's'
      } remain represented in the current response snapshot.`
    )
  }

  if (data.state.population_demands) {
    const { demand_level, source } = data.state.population_demands
    const pop = data.state.estimated_affected_population
    finalStateSentences.push(
      data.state.population_summary ??
        `Population demand estimated as ${demand_level}${
          pop ? ` with approximately ${pop.toLocaleString()} people affected` : ''
        } (source: ${source}).`
    )
  }

  if (mentionsRouting || data.state.routes.length || data.state.blocked_routes.length) {
    if (data.state.routes.length) {
      finalStateSentences.push(
        `${data.state.routes.length} route option${
          data.state.routes.length === 1 ? '' : 's'
        } were produced${
          bestRoute
            ? `; best route is to ${bestRouteHospital ? `"${bestRouteHospital}"` : 'the selected hospital'} at ${bestRoute}`
            : ''
        }.`
      )
    } else if (mentionsRouting) {
      finalStateSentences.push(
        `Routing was relevant for this emergency, but no route options were produced in the final state yet.`
      )
    }

    if (data.state.blocked_routes.length) {
      const detection = data.state.blocked_route_detection
      const sourceText = detection?.source ? ` from ${detection.source}` : ''
      const simulatedText = detection?.simulated ? ' as risk-based candidates' : ''
      finalStateSentences.push(
        `Blocked corridors were identified${sourceText}${simulatedText}${
          topBlockedRoutes ? `, including ${topBlockedRoutes}` : ''
        }.`
      )
    }
  }

  if (!finalStateSentences.length) {
    finalStateSentences.push(
      `The final state contains the current response snapshot, but this run did not return strong hospital, shelter, or routing outputs to summarize yet.`
    )
  }

  return {
    input: {
      overview: (
        <p>
          The pipeline ingested the emergency report and broke it into {chunkCount(data.message)} usable
          context segment{chunkCount(data.message) === 1 ? '' : 's'} so later stages could reason over
          location, urgency, injuries, and displacement details without losing the original message.
        </p>
      ),
      details: <JsonBlock value={{ message: data.message }} />,
      math: (
        <FormulaFlow
          title="Context Encoding"
          accent="#0ea5e9"
          equation="h₀ = encode(split(message))"
          steps={[
            { label: 'Tokenize report', value: `${chunkCount(data.message)} semantic chunk${chunkCount(data.message) === 1 ? '' : 's'}` },
            { label: 'Keep location signal', value: data.state.resolved_location?.query ?? 'location inferred downstream' },
            { label: 'Seed pipeline state', value: 'message → router context vector' },
          ]}
          metrics={[
            { label: 'characters', value: data.message.length },
            { label: 'chunks', value: chunkCount(data.message) },
          ]}
        />
      ),
    },
    router: {
      overview: (
        <div>
          <p style={{ margin: 0 }}>
            The router looked at the emergency description and decided the main operational focus should
            be {data.router.top ? `"${data.router.top}"` : 'the highest ranked task available'}.
            {topTasks
              ? ` It also surfaced related priorities such as ${topTasks}.`
              : ' No additional task candidates were returned in this run.'}
            {data.router.rl.action
              ? ` The RL policy selected "${data.router.rl.action}" and ${data.router.rl.injected ? 'injected it into' : 'aligned with'} the final route set.`
              : ''}
          </p>
          <ExecutionOrder title="Task Priority Order" steps={routerPriorityOrder} />
        </div>
      ),
      details: <JsonBlock value={data.router} />,
      math: (
        <FormulaFlow
          title="Task Routing"
          accent="#2563eb"
          equation="tasks = {t | σ(Wᵣh₀ + bᵣ) ≥ τ} ∪ πᴿᴸ(h₀)"
          steps={[
            { label: 'Score task families', value: data.router.scores.slice(0, 3).map((row) => `${row.task}:${formatScore(row.score)}`).join(' · ') || 'no scores' },
            { label: 'Apply threshold', value: `${data.router.tasks.length} task${data.router.tasks.length === 1 ? '' : 's'} selected` },
            { label: 'RL adjustment', value: data.router.rl.action ? `${data.router.rl.action}${data.router.rl.injected ? ' injected' : ' aligned'}` : 'no RL action' },
          ]}
          metrics={[
            { label: 'top', value: data.router.top ?? 'none' },
            { label: 'top score', value: topRouterScore != null ? formatScore(topRouterScore) : 'n/a' },
            { label: 'source', value: data.router.rl.source ?? 'classifier' },
          ]}
        />
      ),
    },
    planner: {
      overview: (
        <div>
          <p style={{ margin: 0 }}>
            The planner converted the routed task into an execution plan of {data.planner.nodes.length}{' '}
            node{data.planner.nodes.length === 1 ? '' : 's'}. It gave highest priority to{' '}
            {data.planner.top ? `"${data.planner.top}"` : 'the top ranked action'}.
            {plannerPreview
              ? ` The first actions it wants to work through are ${plannerPreview}.`
              : ' The returned plan did not include a previewable action list yet.'}
          </p>
          <ExecutionOrder title="Planned Order" steps={plannerOrder} />
        </div>
      ),
      details: <JsonBlock value={data.planner} />,
      math: (
        <FormulaFlow
          title="Node Planning"
          accent="#7c3aed"
          equation="P(nodeᵢ) = σ(Transformer([tasks; message])ᵢ)"
          steps={[
            { label: 'Fuse intent and text', value: `${data.router.tasks.length} routed task signals` },
            { label: 'Rank reasoning nodes', value: data.planner.scores.slice(0, 3).map((row) => `${row.node}:${formatScore(row.score)}`).join(' · ') || 'no node scores' },
            { label: 'Emit plan set', value: `${data.planner.nodes.length} node${data.planner.nodes.length === 1 ? '' : 's'} selected` },
          ]}
          metrics={[
            { label: 'top node', value: data.planner.top ?? 'none' },
            { label: 'top score', value: topPlannerScore != null ? formatScore(topPlannerScore) : 'n/a' },
          ]}
        />
      ),
    },
    slr: {
      overview: (
        <div>
          <p style={{ margin: 0 }}>
            The SLR graph turned that plan into a dependency-aware reasoning flow with {data.slr.nodes.length}{' '}
            nodes and {data.slr.edges.length} edges. It resolved the order of work so upstream decisions
            happen before downstream actions
            {topSlrOrder ? `, beginning with ${topSlrOrder}.` : '.'}
          </p>
          <ExecutionOrder title="Resolved Order" steps={slrResolvedOrder} />
        </div>
      ),
      details: <JsonBlock value={data.slr} />,
      math: (
        <FormulaFlow
          title="Symbolic Dependency Resolution"
          accent="#8b5cf6"
          equation="G = (V, E), order = topo_sort(G)"
          steps={[
            { label: 'Create node set', value: `|V| = ${data.slr.nodes.length}` },
            { label: 'Attach dependency edges', value: `|E| = ${data.slr.edges.length}` },
            { label: 'Resolve execution order', value: data.slr.order.slice(0, 4).join(' → ') || 'no order' },
          ]}
          metrics={[
            { label: 'nodes', value: data.slr.nodes.length },
            { label: 'edges', value: data.slr.edges.length },
            { label: 'first', value: data.slr.order[0] ?? 'n/a' },
          ]}
        />
      ),
    },
    executor: {
      overview: (
        <div>
          <p style={{ margin: 0 }}>
            The executor walked through {data.executor.timeline.length} planned step
            {data.executor.timeline.length === 1 ? '' : 's'} and finished with a{' '}
            {`"${data.executor.status}"`} run state. So far, {completedSteps} step
            {completedSteps === 1 ? '' : 's'} completed, {skippedSteps} were skipped, and {failedSteps}{' '}
            failed
            {topTimelineNodes ? ` while processing actions like ${topTimelineNodes}.` : '.'}
          </p>
          <ExecutionOrder
            title="Executed Steps"
            steps={executorOrder}
          />
        </div>
      ),
      details: <JsonBlock value={data.executor} />,
      math: (
        <FormulaFlow
          title="State Transition Execution"
          accent="#059669"
          equation="Sₜ₊₁ = toolₙ(Sₜ, context)"
          steps={[
            { label: 'Read graph order', value: `${data.executor.timeline.length} scheduled step${data.executor.timeline.length === 1 ? '' : 's'}` },
            { label: 'Mutate environment', value: topTimelineNodes ? `recent nodes: ${topTimelineNodes}` : 'waiting for trace' },
            { label: 'Collect trace', value: `${completedSteps} completed · ${skippedSteps} skipped · ${failedSteps} failed` },
          ]}
          metrics={[
            { label: 'status', value: data.executor.status },
            { label: 'completed', value: completedSteps },
            { label: 'skipped', value: skippedSteps },
          ]}
        />
      ),
    },
    verifier: {
      overview: (
        <p>
          The verifier reviewed the executed plan and returned an overall{' '}
          {data.verifier.valid ? 'valid' : 'invalid'} outcome. The rule check{' '}
          {data.verifier.rule ? 'passed' : 'failed'}, the model-based validation{' '}
          {data.verifier.gemini ? 'passed' : 'failed'}, and the main explanation was:{' '}
          {data.verifier.reason || 'No verifier explanation was returned.'}
        </p>
      ),
      details: <JsonBlock value={data.verifier} />,
      math: (
        <FormulaFlow
          title="Verification Fusion"
          accent="#e11d48"
          equation="valid = rule_check(S*) ∧ model_validate(trace, S*)"
          steps={[
            { label: 'Rule checker', value: data.verifier.rule ? 'passed' : 'failed' },
            { label: 'Model verifier', value: data.verifier.gemini ? 'passed' : 'failed' },
            { label: 'Final verdict', value: data.verifier.valid ? 'valid response state' : 'invalid response state' },
          ]}
          metrics={[
            { label: 'rule', value: data.verifier.rule ? 'true' : 'false' },
            { label: 'gemini', value: data.verifier.gemini ? 'true' : 'false' },
            { label: 'valid', value: data.verifier.valid ? 'true' : 'false' },
          ]}
        />
      ),
    },
    final: {
      overview: (
        <div style={{ display: 'grid', gap: 10 }}>
          {finalStateSentences.map((sentence, index) => (
            <p key={`final-state-${index}`} style={{ margin: 0 }}>
              {sentence}
            </p>
          ))}
        </div>
      ),
      details: <JsonBlock value={data.state} />,
      math: (
        <FormulaFlow
          title="Final State Synthesis"
          accent="#6d28d9"
          equation="S* = aggregate(hospitals, Dijkstra(G), Σ raster cells)"
          steps={[
            { label: 'Nearest hospital candidates', value: `${data.state.hospitals.length} hospital option${data.state.hospitals.length === 1 ? '' : 's'}` },
            { label: 'Dijkstra route selection', value: bestRouteHospital ? `${bestRouteHospital} · ${bestRouteDistance}` : bestRouteDistance },
            { label: 'Raster demand estimate', value: `${data.state.estimated_affected_population?.toLocaleString() ?? 'unknown'} affected · radius ${rasterRadius ?? 'n/a'} km` },
          ]}
          metrics={[
            { label: 'best hospital', value: bestRouteHospital ?? 'n/a' },
            { label: 'route', value: bestRouteDistance },
            { label: 'population source', value: rasterSource },
          ]}
        />
      ),
    },
  }
}
