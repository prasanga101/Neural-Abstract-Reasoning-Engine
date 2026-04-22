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
    routes: [],
    best_route: null,
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
  if (typeof route.distance === 'number') parts.push(`${roundNumber(route.distance)} km`)
  if (typeof route.duration === 'number') parts.push(`${roundNumber(route.duration)} min`)
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
      routes: asArray(state.routes),
      best_route: asObject(state.best_route),
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
        <p>
          Input text is prepared as a context signal for the rest of the pipeline. The frontend will
          faithfully display whatever normalized pipeline JSON you send for this stage.
        </p>
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
        <div>
          <p style={{ margin: 0 }}>
            Router results are rendered directly from the JSON payload: predicted tasks, sorted scores,
            the promoted top intent, and RL routing metadata when present.
          </p>
          {data.router.rl.action ? (
            <p style={{ margin: '8px 0 0' }}>
              RL source: {data.router.rl.source ?? 'unknown'}
              {rlClassifierTasks ? ` · classifier candidates: ${rlClassifierTasks}` : ''}
            </p>
          ) : null}
        </div>
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
        <p>
          Planner display is derived from the real planner JSON: predicted nodes, score ordering, and
          the chosen top action for execution.
        </p>
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
        <p>
          SLR phase is visualized from the graph JSON itself: node set, dependency edges, and the final
          execution order emitted by your symbolic reasoning layer.
        </p>
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
        <p>
          Execution details are generated from the live trace JSON, so each step, node name, and status
          reflects the actual run you provide.
        </p>
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
        <p>
          Verifier output is read straight from the JSON payload, including overall validity, per-check
          results, and the explanation text.
        </p>
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
        <p>
          Final state content comes from the returned environment snapshot, including route options,
          hospital metadata, blocked routes, and the selected best route.
        </p>
      ),
    },
  }
}
