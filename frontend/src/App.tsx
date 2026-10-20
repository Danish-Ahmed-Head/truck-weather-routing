import { useEffect, useRef, useState } from "react";
import { planRoutes } from "./api";
import MapView from "./MapView";
import { LEVEL_COLORS, LEVEL_LABELS, fmtDuration, fmtTime, routeColor } from "./risk";
import type { PlanResponse, Route } from "./types";

function defaultDeparture(): string {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setMinutes(0, 0, 0);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

function RiskBar({ route }: { route: Route }) {
  const s = route.stats;
  const parts = [s.low_miles, s.moderate_miles, s.high_miles, s.severe_miles, s.no_travel_miles];
  return (
    <div className="riskbar" title={parts.map((v, i) => `${LEVEL_LABELS[i]} ${v} mi`).join(" · ")}>
      {parts.map((v, i) => (
        <span key={i} style={{ width: `${(v / route.distance_mi) * 100}%`, background: LEVEL_COLORS[i] }} />
      ))}
    </div>
  );
}

function RouteCard({ route, selected, onSelect }: { route: Route; selected: boolean; onSelect: () => void }) {
  const s = route.stats;
  return (
    <button className={`route-card${selected ? " selected" : ""}`} onClick={onSelect} aria-pressed={selected}>
      <div className="route-head">
        <span className="swatch" style={{ background: routeColor(route.id) }} />
        <strong>{route.name}</strong>
        {route.recommended && <span className="badge">Recommended</span>}
        <span className="rank">#{route.rank}</span>
      </div>
      <div className="route-sub">{route.summary}</div>
      <div className="route-stats">
        <span>{route.distance_mi} mi</span>
        <span>{fmtDuration(route.duration_h)}</span>
        <span>Arrive {fmtTime(route.arrival)}</span>
      </div>
      <RiskBar route={route} />
      <div className="route-risk">
        <span>Severe+ {(s.severe_miles + s.no_travel_miles).toFixed(0)} mi</span>
        <span>High {s.high_miles.toFixed(0)} mi</span>
        <span>Avg risk {s.avg_risk.toFixed(2)}</span>
        <span style={{ color: LEVEL_COLORS[s.max_level] }}>Worst: {LEVEL_LABELS[s.max_level]}</span>
      </div>
      {route.recommended && route.reason && <div className="reason">{route.reason}</div>}
    </button>
  );
}

function CheckpointTable({ route }: { route: Route }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Mile</th><th>ETA</th><th>Wind</th><th>Rain</th><th>Snow</th><th>Risk</th></tr>
        </thead>
        <tbody>
          {route.checkpoints.map((c) => (
            <tr key={c.mile}>
              <td>{c.mile}</td>
              <td>{fmtTime(c.eta)}</td>
              <td>{c.wind_mph}</td>
              <td>{c.rain_in_hr}</td>
              <td>{c.snow_in_hr}</td>
              <td><span className="chip" style={{ background: LEVEL_COLORS[c.level] }}>{c.label}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [origin, setOrigin] = useState("Denver, CO");
  const [destination, setDestination] = useState("Omaha, NE");
  const [departure, setDeparture] = useState(defaultDeparture);
  const [load, setLoad] = useState("35000");
  const [interval, setInterval_] = useState<"auto" | "10" | "25" | "50">("auto");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PlanResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hour, setHour] = useState(0);
  const [showHeat, setShowHeat] = useState(true);
  const [playing, setPlaying] = useState(false);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setHour((h) => (h >= 48 ? 0 : h + 1)), 350);
    return () => window.clearInterval(timer);
  }, [playing]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    abort.current?.abort();
    abort.current = new AbortController();
    setBusy(true);
    setError(null);
    try {
      const result = await planRoutes(
        {
          origin,
          destination,
          departure: new Date(departure).toISOString(),
          load_lb: Number(load),
          interval: interval === "auto" ? "auto" : (Number(interval) as 10 | 25 | 50),
        },
        abort.current.signal,
      );
      setData(result);
      setSelectedId(result.routes.find((r) => r.recommended)?.id ?? result.routes[0].id);
      setHour(0);
    } catch (err) {
      if ((err as Error).name !== "AbortError") setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const selected = data?.routes.find((r) => r.id === selectedId) ?? null;
  const clock = data ? fmtTime(new Date(new Date(data.departure).getTime() + hour * 3600 * 1000).toISOString()) : "";

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Weather-Aware Truck Routing</h1>
        <form onSubmit={submit}>
          <label>Origin<input value={origin} onChange={(e) => setOrigin(e.target.value)} required /></label>
          <label>Destination<input value={destination} onChange={(e) => setDestination(e.target.value)} required /></label>
          <div className="row">
            <label>Departure<input type="datetime-local" value={departure} onChange={(e) => setDeparture(e.target.value)} required /></label>
            <label>Load (lb)<input type="number" min={0} max={150000} step={500} value={load} onChange={(e) => setLoad(e.target.value)} required /></label>
          </div>
          <label>Weather checkpoints
            <select value={interval} onChange={(e) => setInterval_(e.target.value as typeof interval)}>
              <option value="auto">Auto (10 / 25 / 50 mi by trip length)</option>
              <option value="10">Every 10 miles</option>
              <option value="25">Every 25 miles</option>
              <option value="50">Every 50 miles</option>
            </select>
          </label>
          <button className="primary" disabled={busy}>{busy ? "Finding routes…" : "Find safest route"}</button>
        </form>
        {error && <div className="error" role="alert">{error}</div>}
        {data && (
          <>
            <p className="trip">{data.origin.name.split(",")[0]} → {data.destination.name.split(",")[0]} · departs {fmtTime(data.departure)}</p>
            <div className="routes">
              {[...data.routes].sort((a, b) => a.rank - b.rank).map((r) => (
                <RouteCard key={r.id} route={r} selected={r.id === selectedId} onSelect={() => setSelectedId(r.id)} />
              ))}
            </div>
            {selected && (
              <>
                <h2>{selected.name} checkpoints (every {selected.interval_mi} mi)</h2>
                <CheckpointTable route={selected} />
              </>
            )}
          </>
        )}
      </aside>
      <main className="map-wrap">
        <MapView data={data} selectedId={selectedId} hour={hour} showHeat={showHeat} onSelect={setSelectedId} />
        {data && (
          <div className="heat-panel">
            <div className="heat-top">
              <label className="toggle"><input type="checkbox" checked={showHeat} onChange={(e) => setShowHeat(e.target.checked)} /> Weather heatmap</label>
              <strong>+{hour} h · {clock}</strong>
              <button type="button" onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Play"}</button>
            </div>
            <input type="range" min={0} max={48} value={hour} onChange={(e) => setHour(Number(e.target.value))} aria-label="Forecast hour after departure" />
            <div className="legend">
              {LEVEL_LABELS.map((l, i) => (
                <span key={l}><i style={{ background: LEVEL_COLORS[i] }} />{l}</span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
