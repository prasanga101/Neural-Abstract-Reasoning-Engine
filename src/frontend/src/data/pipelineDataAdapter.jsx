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
    valid: null,
    status: 'indeterminate',
    rule: false,
    gemini: null,
    gemini_available: false,
    gemini_error_type: null,
    retry_after_seconds: null,
    reason: '',
  },
  state: {
    ambulances: 0,
    ambulances_dispatched: 0,
    shelters: 0,
    shelters_allocated: 0,
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
          ? route.distance
          : null
  const durationMin =
    typeof route.duration_min === 'number'
      ? route.duration_min
      : typeof route.duration_s === 'number'
        ? route.duration_s / 60
        : typeof route.duration === 'number'
          ? route.duration
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

const mathSections = {
  input: (
    <div className="space-y-2">
      <p>Message is split into emergency facts while preserving location, injury, shelter, and routing signals.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'chunks = split(message, /[,.!?]/)\ncontext = normalize(location + urgency + needs)\nstate_0 = { message, context }'}
      </code>
    </div>
  ),
  router: (
    <div className="space-y-2">
      <p>Router combines classifier scores with emergency keywords so medical, shelter, and routing work stay in the plan.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'scores = classifier(context)\ntasks = { t | score(t) >= threshold }\nmedical_terms -> add hospital + ambulance\nroute_terms -> add blocked-route scan + route planning'}
      </code>
    </div>
  ),
  planner: (
    <div className="space-y-2">
      <p>Planner expands routed tasks into executable nodes and ranks urgent operational work first.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'nodes = expand(tasks)\npriority(node) = severity_weight + dependency_weight\nplan = sort(nodes, priority desc)'}
      </code>
    </div>
  ),
  slr: (
    <div className="space-y-2">
      <p>SLR resolves dependencies so hospital lookup, route planning, ambulance dispatch, and shelter allocation run in a valid order.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'G = (V, E)\nidentify_nearest_hospitals -> dispatch_ambulances\ncollect_sensor_data -> identify_alternative_routes\norder = topological_sort(G)'}
      </code>
    </div>
  ),
  executor: (
    <div className="space-y-2">
      <p>Executor merges every tool result into the tracked emergency state and records the timeline outcome.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'for node in order:\n  result = run_tool(node, state_t)\n  state_t+1 = merge(state_t, result.updates)\n  timeline += { node, status, result }'}
      </code>
    </div>
  ),
  verifier: (
    <div className="space-y-2">
      <p>Verifier combines deterministic resource rules with local Ollama validation; used resources are valid as long as counts are nonnegative.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'rule_ok = ambulances >= 0 AND shelters >= 0\nmodel_ok = ollama_validate(trace, final_state)\nvalid = rule_ok AND model_ok'}
      </code>
    </div>
  ),
  final: (
    <div className="space-y-2">
      <p>Final state is assembled from hospital candidates, Dijkstra/OSRM route costs, blocked-route scan results, and allocated resources.</p>
      <code className="block rounded bg-slate-100 p-2 text-xs">
        {'hospitals = nearest(event_coordinates, hospital_index)\nblocked_edges = scan_roads(event_coordinates)\nif blocked_edges is empty: blocked_routes = []\nbest_route = min(Dijkstra(graph, event, hospital) for hospital in hospitals)\nstate* = { hospitals, best_route, blocked_routes, ambulances, shelters }'}
      </code>
    </div>
  ),
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
      valid: typeof verifier.valid === 'boolean' ? verifier.valid : null,
      status:
        typeof verifier.status === 'string'
          ? verifier.status
          : verifier.valid === null || verifier.valid === undefined
            ? 'indeterminate'
            : verifier.valid
              ? 'valid'
              : 'invalid',
      rule: Boolean(verifier.rule),
      llm:
        typeof verifier.llm === 'boolean'
          ? verifier.llm
          : typeof verifier.gemini === 'boolean'
            ? verifier.gemini
            : null,
      gemini:
        typeof verifier.gemini === 'boolean'
          ? verifier.gemini
          : typeof verifier.llm === 'boolean'
            ? verifier.llm
            : null,
      gemini_available: verifier.gemini_available !== false,
      gemini_error_type:
        typeof verifier.gemini_error_type === 'string' ? verifier.gemini_error_type : null,
      retry_after_seconds:
        typeof verifier.retry_after_seconds === 'number' ? verifier.retry_after_seconds : null,
      reason: typeof verifier.reason === 'string' ? verifier.reason : '',
    },
    state: {
      ambulances: typeof state.ambulances === 'number' ? state.ambulances : 0,
      ambulances_dispatched:
        typeof state.ambulances_dispatched === 'number' ? state.ambulances_dispatched : 0,
      shelters: typeof state.shelters === 'number' ? state.shelters : 0,
      shelters_allocated: typeof state.shelters_allocated === 'number' ? state.shelters_allocated : 0,
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
  if (id === 'verifier') {
    if (data.verifier.valid === null) return 'indeterminate'
    return data.verifier.valid ? 'passed ✓' : 'failed ✗'
  }
  return `${data.state.routes.length} routes`
}

export function buildPipelineSections(rawData) {
  const data = normalizePipelineData(rawData)
  const completedSteps = data.executor.timeline.filter((step) => step.status === 'completed').length
  const skippedSteps = data.executor.timeline.filter((step) => step.status === 'skipped').length
  const failedSteps = data.executor.timeline.filter((step) => step.status === 'failed').length
  const bestRoute = formatRoute(data.state.best_route)
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
      if (data.state.ambulances_dispatched) {
        finalStateSentences.push(
          `${data.state.ambulances_dispatched} ambulance${
            data.state.ambulances_dispatched === 1 ? '' : 's'
          } were dispatched; ${data.state.ambulances} remain available.`
        )
      } else {
        finalStateSentences.push(
          `${data.state.ambulances} ambulance${
            data.state.ambulances === 1 ? '' : 's'
          } remain available in the tracked state after execution.`
        )
      }
    }
  }

  if (mentionsShelter || data.state.shelters) {
    if (data.state.shelters_allocated) {
      finalStateSentences.push(
        `${data.state.shelters_allocated} shelter${
          data.state.shelters_allocated === 1 ? '' : 's'
        } were allocated; ${data.state.shelters} remain available.`
      )
    } else {
      finalStateSentences.push(
        `${data.state.shelters} shelter${
          data.state.shelters === 1 ? '' : 's'
        } remain represented in the current response snapshot.`
      )
    }
  }

  if (mentionsRouting || data.state.routes.length || data.state.blocked_routes.length) {
    if (data.state.routes.length) {
      finalStateSentences.push(
        `${data.state.routes.length} route option${
          data.state.routes.length === 1 ? '' : 's'
        } were produced${bestRoute ? `, with a best route of ${bestRoute}` : ''}.`
      )
    } else if (mentionsRouting) {
      finalStateSentences.push(
        `Routing was relevant for this emergency, but no route options were produced in the final state yet.`
      )
    }

    if (data.state.blocked_routes.length) {
      finalStateSentences.push(
        `Blocked corridors were identified${topBlockedRoutes ? `, including ${topBlockedRoutes}` : ''}.`
      )
    } else if (mentionsRouting || data.state.routes.length) {
      finalStateSentences.push(
        data.state.blocked_route_detection?.message || 'No routes are blocked in the current response snapshot.'
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
      math: mathSections.input,
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
      math: mathSections.router,
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
      math: mathSections.planner,
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
      math: mathSections.slr,
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
      math: mathSections.executor,
    },
    verifier: {
      overview: (
        <p>
          The verifier reviewed the executed plan and returned an overall{' '}
          {data.verifier.status || (data.verifier.valid === null ? 'indeterminate' : data.verifier.valid ? 'valid' : 'invalid')}{' '}
          outcome. The rule check{' '}
          {data.verifier.rule ? 'passed' : 'failed'}, the model-based validation{' '}
          {data.verifier.gemini_available
            ? data.verifier.llm
              ? 'passed'
              : 'failed'
            : 'was unavailable'}
          , and the main explanation was:{' '}
          {data.verifier.reason || 'No verifier explanation was returned.'}
        </p>
      ),
      details: <JsonBlock value={data.verifier} />,
      math: mathSections.verifier,
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
      math: mathSections.final,
    },
  }
}
