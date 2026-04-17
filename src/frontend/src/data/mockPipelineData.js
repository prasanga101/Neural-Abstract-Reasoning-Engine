export const mockPipelineData = {
  message:
    'Flash flooding reported near Riverside district. Need evacuation guidance for low-lying zones and ambulance routing.',
  router: {
    tasks: ['Evacuation Planning', 'Ambulance Routing', 'Shelter Allocation'],
    scores: [
      { task: 'Evacuation Planning', score: 0.98 },
      { task: 'Ambulance Routing', score: 0.95 },
      { task: 'Shelter Allocation', score: 0.91 },
      { task: 'Power Grid Recovery', score: 0.44 },
    ],
    top: 'Evacuation Planning',
  },
  planner: {
    nodes: [
      'Assess Flood Depth',
      'Mark Blocked Corridors',
      'Route Medical Teams',
      'Assign Shelters',
    ],
    scores: [
      { node: 'Assess Flood Depth', score: 0.99 },
      { node: 'Route Medical Teams', score: 0.96 },
      { node: 'Assign Shelters', score: 0.94 },
      { node: 'Mark Blocked Corridors', score: 0.92 },
    ],
    top: 'Assess Flood Depth',
  },
  slr: {
    nodes: [
      { id: 'n1', label: 'Ingest Alerts', role: 'context' },
      { id: 'n2', label: 'Route Tasks', role: 'router' },
      { id: 'n3', label: 'Build Plan', role: 'planner' },
      { id: 'n4', label: 'Allocate Teams', role: 'executor' },
      { id: 'n5', label: 'Validate Constraints', role: 'verifier' },
      { id: 'n6', label: 'Publish State', role: 'state' },
    ],
    edges: [
      { source: 'n1', target: 'n2' },
      { source: 'n2', target: 'n3' },
      { source: 'n3', target: 'n4' },
      { source: 'n4', target: 'n5' },
      { source: 'n5', target: 'n6' },
      { source: 'n3', target: 'n5' },
    ],
    order: ['n1', 'n2', 'n3', 'n4', 'n5', 'n6'],
  },
  executor: {
    status: 'completed',
    timeline: [
      { step: 1, node: 'Assess Flood Depth', status: 'completed' },
      { step: 2, node: 'Mark Blocked Corridors', status: 'completed' },
      { step: 3, node: 'Route Medical Teams', status: 'completed' },
      { step: 4, node: 'Assign Shelters', status: 'skipped' },
      { step: 5, node: 'Dispatch Ambulances', status: 'completed' },
    ],
  },
  verifier: {
    valid: true,
    rule: true,
    gemini: true,
    reason:
      'All critical routes have alternatives, shelter occupancy remains below threshold, and ambulance ETA constraints pass policy checks.',
  },
  state: {
    ambulances: 20,
    shelters: 10,
    hospitals: [
      { name: 'Riverside General', lat: 27.703, lon: 85.328 },
      { name: 'North Trauma Unit', lat: 27.719, lon: 85.307 },
    ],
    blocked_routes: ['R-14 Bridge', 'Canal Road Segment C'],
    routes: [
      { distance: 8.2, duration: 16 },
      { distance: 9.5, duration: 18 },
      { distance: 12.3, duration: 24 },
    ],
    best_route: { distance: 8.2, duration: 16 },
  },
}
