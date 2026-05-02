const DEMAND_COLORS = {
  critical: "text-red-600",
  high: "text-orange-500",
  moderate: "text-yellow-600",
  low: "text-green-600",
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-white/65 px-2 py-1.5">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-800">{value}</p>
    </div>
  )
}

function formatRoute(route) {
  const distanceKm =
    typeof route?.distance_km === "number"
      ? route.distance_km
      : typeof route?.distance_m === "number"
        ? route.distance_m / 1000
        : typeof route?.distance === "number"
          ? route.distance / 1000
          : null
  const durationMin =
    typeof route?.duration_min === "number"
      ? route.duration_min
      : typeof route?.duration_s === "number"
        ? route.duration_s / 60
        : typeof route?.duration === "number"
          ? route.duration / 60
          : null

  if (distanceKm == null || durationMin == null) return null
  return `${distanceKm.toFixed(2)} km - ${durationMin.toFixed(1)} min`
}

export function FinalStatePanel({ state }) {
  const demands = state.rasterio_population ?? state.raster_population ?? state.population_demands
  const demandLevel = demands?.demand_level
  const demandColor = DEMAND_COLORS[demandLevel] ?? "text-slate-800"
  const affectedPopulation =
    state.estimated_affected_population ?? demands?.estimated_affected_population
  const bestRoute = state.best_route
  const bestRouteLabel = formatRoute(bestRoute)

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-1.5">
        <Metric label="Ambulances" value={state.ambulances} />
        <Metric label="Shelters" value={state.shelters} />
        <Metric label="Hospitals" value={state.hospitals.length} />
        <Metric label="Blocked" value={state.blocked_routes.length} />
      </div>

      {demands && (
        <div className="rounded-xl border border-slate-200/80 bg-white/65 px-2 py-1.5 text-[11px]">
          <p className="text-[10px] uppercase tracking-wide text-slate-400 mb-0.5">Population Demand</p>
          <div className="flex items-center justify-between">
            <span className={`text-sm font-semibold capitalize ${demandColor}`}>{demandLevel}</span>
            <span className="text-slate-500">
              {affectedPopulation?.toLocaleString() ?? "Unknown"} affected
            </span>
          </div>
          <p className="text-slate-400 mt-0.5">source: {demands.source}</p>
        </div>
      )}

      {bestRouteLabel && (
        <div className="rounded-xl border border-indigo-100/70 bg-white/70 px-2 py-1.5 text-[11px]">
          <p className="text-slate-500">Best route</p>
          {bestRoute.hospital && (
            <p className="truncate font-medium text-slate-700">{bestRoute.hospital}</p>
          )}
          <p className="font-semibold text-indigo-700">
            {bestRouteLabel}
          </p>
        </div>
      )}
    </div>
  )
}
