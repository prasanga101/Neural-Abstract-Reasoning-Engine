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
    infrastructure_damage: {
      level: 'moderate',
      affected_structures: ['R-14 Bridge', 'Canal Road Segment C', 'Riverside residential blocks'],
      road_closures: 2,
      source: 'scan',
    },
    disaster_zone_scan: {
      zones: [
        'Zone A — Riverside district (critical)',
        'Zone B — Low-lying canal area (high risk)',
      ],
      flood_depth_m: 1.8,
      area_km2: 4.2,
      source: 'aerial',
    },
    trapped_victims: {
      count: 34,
      locations: ['Riverside district block 4', 'Canal Road residential sector'],
      severity: 'moderate',
    },
    rescue_teams_allocated: 3,
    hospital_capacity_plan: {
      hospitals: [
        { name: 'Riverside General', available_beds: 45, icu_beds: 8 },
        { name: 'North Trauma Unit', available_beds: 30, icu_beds: 12 },
      ],
      overflow_plan: 'Redirect to Patan Hospital if occupancy exceeds 80%',
    },
    resource_allocation_plan: {
      ambulances_dispatched: 15,
      shelters_allocated: 3,
      food_supplies: 450,
      water_supplies: 600,
      medical_supplies: 300,
      relief_resources: 2000,
    },
    information_summary: {
      summary:
        'Flash flooding in Riverside district. 2 corridors blocked. 34 trapped victims identified. Moderate injury severity. 15 ambulances dispatched to low-lying zones.',
      disaster_type: 'flood',
      location: 'Riverside district, Kathmandu',
      affected_population: 'medium',
      immediate_needs: ['medical', 'shelter', 'rescue', 'water'],
    },
    public_report: {
      title: 'Flash Flood Emergency — Riverside District',
      issued_at: '2026-05-28T09:00:00Z',
      status: 'active',
      advice:
        'Residents in low-lying zones must evacuate immediately. Avoid R-14 Bridge and Canal Road Segment C. Emergency shelters are open at designated assembly points.',
      contact: 'Emergency: 100',
    },
    population_demands: {
      demand_level: 'moderate',
      source: 'PopulationDemandsEstimateTool',
    },
    estimated_affected_population: 85240,
    raster_population: {
      radius_km: 5,
      source: 'WorldPop GPWv4',
      total_population: 85240,
      cell_resolution_m: 100,
    },
    rasterio_population: {
      radius_km: 5,
      source: 'WorldPop GPWv4',
      total_population: 85240,
      cell_resolution_m: 100,
      lat: 27.703,
      lon: 85.328,
    },
    population_summary:
      'Raster scan estimates ~85,240 people within 5 km of the event epicentre (WorldPop GPWv4). Demand classified as moderate.',
  },
}
