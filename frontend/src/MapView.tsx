import L from "leaflet";
import { useEffect, useMemo, useRef } from "react";
import { buildSamples, sampleLevels } from "./heat";
import { checkpointColor, fmtNum, fmtTime, levelColor, routeColor } from "./risk";
import type { PlanResponse, Route } from "./types";

interface Props {
  data: PlanResponse | null;
  selectedId: string | null;
  hour: number;
  showHeat: boolean;
  onSelect: (id: string) => void;
}

const HEAT_PANE = "heat";

/** Leaflet treats string tooltips as HTML; place names come from a third party, so pass a text node instead. */
function plainText(text: string): HTMLElement {
  const el = document.createElement("span");
  el.textContent = text;
  return el;
}

function popupHtml(route: Route, idx: number): string {
  const c = route.checkpoints[idx];
  const drivers = c.drivers.length ? `<div>${c.drivers.join("; ")}</div>` : "";
  const warn = c.forecast_beyond_range ? "<div><i>Beyond forecast range</i></div>" : "";
  return `<b>${route.name} · mile ${c.mile}</b><br/>ETA ${fmtTime(c.eta)}<br/>
    <b style="color:${checkpointColor(c)}">${c.label}</b>${drivers}
    Wind ${fmtNum(c.wind_mph)} mph · Rain ${fmtNum(c.rain_in_hr)} in/hr · Snow ${fmtNum(c.snow_in_hr)} in/hr${warn}`;
}

export default function MapView({ data, selectedId, hour, showHeat, onSelect }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const routeLayer = useRef(L.layerGroup());
  const pointLayer = useRef(L.layerGroup());
  const heat = useRef(L.layerGroup());
  const heatSegments = useRef<L.Polyline[]>([]);
  const heatRenderer = useRef<L.Canvas | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  const samples = useMemo(() => (data ? buildSamples(data.routes) : []), [data]);

  useEffect(() => {
    if (!host.current || map.current) return;
    const m = L.map(host.current, { preferCanvas: true }).setView([39.5, -98.35], 4);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(m);
    routeLayer.current.addTo(m);
    // Own pane + canvas renderer; the CSS blur (see styles.css) turns the coloured segments into a soft corridor.
    m.createPane(HEAT_PANE).style.zIndex = "350";
    heatRenderer.current = L.canvas({ pane: HEAT_PANE, padding: 0.5 });
    pointLayer.current.addTo(m);
    map.current = m;
    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  // Route lines + endpoints; refit only when a new result arrives.
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    routeLayer.current.clearLayers();
    if (!data) return;
    for (const route of data.routes) {
      const selected = route.id === selectedId;
      const line = L.polyline(route.geometry, {
        color: routeColor(route.id),
        weight: selected ? 7 : 4,
        opacity: selected ? 0.95 : 0.55,
        dashArray: route.recommended ? undefined : "8 6",
      });
      line.bindTooltip(`${route.name}${route.recommended ? " (recommended)" : ""}`, { sticky: true });
      line.on("click", () => onSelectRef.current(route.id));
      routeLayer.current.addLayer(line);
      if (selected) line.bringToFront();
    }
    for (const [pt, label] of [[data.origin, "Origin"], [data.destination, "Destination"]] as const) {
      L.circleMarker([pt.lat, pt.lon], { radius: 9, color: "#111", weight: 3, fillColor: "#fff", fillOpacity: 1 })
        .bindTooltip(plainText(`${label}: ${pt.name}`))
        .addTo(routeLayer.current);
    }
  }, [data, selectedId]);

  useEffect(() => {
    const m = map.current;
    if (!m || !data) return;
    const all = data.routes.flatMap((r) => r.geometry);
    // Extra room at the bottom keeps the route clear of the floating heatmap panel.
    m.fitBounds(L.latLngBounds(all as L.LatLngTuple[]), { paddingTopLeft: [40, 40], paddingBottomRight: [40, 150] });
  }, [data]);

  // Checkpoint dots for the selected route only, to keep the map readable.
  useEffect(() => {
    pointLayer.current.clearLayers();
    const route = data?.routes.find((r) => r.id === selectedId);
    if (!route) return;
    route.checkpoints.forEach((c, idx) => {
      L.circleMarker([c.lat, c.lon], {
        radius: 7,
        color: "#fff",
        weight: 2,
        fillColor: checkpointColor(c),
        fillOpacity: 1,
      })
        .bindPopup(popupHtml(route, idx))
        .bindTooltip(`Mile ${c.mile}: ${c.label}`)
        .addTo(pointLayer.current);
    });
  }, [data, selectedId]);

  // Build one short coloured segment per sample whenever a new result arrives.
  useEffect(() => {
    heat.current.clearLayers();
    heatSegments.current = [];
    const m = map.current;
    if (!m || !samples.length) return;
    const renderer = heatRenderer.current!;
    const segs: L.Polyline[] = [];
    samples.forEach((p, k) => {
      const next = samples[k + 1];
      if (!next || next.route !== p.route) return;
      const seg = L.polyline(
        [[p.lat, p.lon], [next.lat, next.lon]],
        { renderer, pane: HEAT_PANE, weight: 30, lineCap: "round", opacity: 0.55, interactive: false },
      );
      seg.addTo(heat.current);
      segs.push(seg);
    });
    heatSegments.current = segs;
  }, [samples]);

  // The slider only restyles existing segments (no layer churn); Leaflet batches the canvas redraw.
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    if (!showHeat) {
      if (m.hasLayer(heat.current)) m.removeLayer(heat.current);
      return;
    }
    if (!m.hasLayer(heat.current)) heat.current.addTo(m);
    const levels = sampleLevels(samples, hour);
    heatSegments.current.forEach((seg, k) => {
      const [a, b] = [levels[k], levels[k + 1]];
      seg.setStyle({ color: levelColor(a < 0 || b < 0 ? -1 : (a + b) / 2) });
    });
  }, [samples, hour, showHeat]);

  return <div ref={host} className="map" />;
}
