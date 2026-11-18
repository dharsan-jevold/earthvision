import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { Map as MLMap, MapMouseEvent, GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useAppStore } from "../store/useAppStore";

// Free, keyless raster basemap so the map works with zero API credentials.
const STYLE = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};

export default function MapSelector() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const drawing = useRef(false);
  const startLngLat = useRef<[number, number] | null>(null);
  const [areaKm2, setAreaKm2] = useState<number | null>(null);

  const setBBox = useAppStore((s) => s.setBBox);
  const bbox = useAppStore((s) => s.bbox);
  const layers = useAppStore((s) => s.layers);
  const activeLayer = useAppStore((s) => s.activeLayer);

  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: STYLE,
      center: [80.25, 13.05], // Chennai — sensible default, user can pan anywhere
      zoom: 10,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      map.addSource("selection", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "selection-fill",
        type: "fill",
        source: "selection",
        paint: { "fill-color": "#22d3ee", "fill-opacity": 0.15 },
      });
      map.addLayer({
        id: "selection-line",
        type: "line",
        source: "selection",
        paint: { "line-color": "#22d3ee", "line-width": 2 },
      });
      setMapLoaded(true);
    });

    const rectFeature = (a: [number, number], b: [number, number]) => {
      const minLon = Math.min(a[0], b[0]);
      const maxLon = Math.max(a[0], b[0]);
      const minLat = Math.min(a[1], b[1]);
      const maxLat = Math.max(a[1], b[1]);
      return {
        type: "FeatureCollection" as const,
        features: [
          {
            type: "Feature" as const,
            properties: {},
            geometry: {
              type: "Polygon" as const,
              coordinates: [
                [
                  [minLon, minLat],
                  [maxLon, minLat],
                  [maxLon, maxLat],
                  [minLon, maxLat],
                  [minLon, minLat],
                ],
              ],
            },
          },
        ],
      };
    };

    const areaKm2Of = (a: [number, number], b: [number, number]) => {
      const minLon = Math.min(a[0], b[0]);
      const maxLon = Math.max(a[0], b[0]);
      const minLat = Math.min(a[1], b[1]);
      const maxLat = Math.max(a[1], b[1]);
      const latMid = (minLat + maxLat) / 2;
      const kmPerDegLat = 111.32;
      const kmPerDegLon = 111.32 * Math.cos((latMid * Math.PI) / 180);
      return Math.abs(maxLon - minLon) * kmPerDegLon * Math.abs(maxLat - minLat) * kmPerDegLat;
    };

    map.on("mousedown", (e: MapMouseEvent) => {
      if (!e.originalEvent.shiftKey) return; // shift+drag to draw, so normal pan still works
      drawing.current = true;
      startLngLat.current = [e.lngLat.lng, e.lngLat.lat];
      map.dragPan.disable();
    });

    map.on("mousemove", (e: MapMouseEvent) => {
      if (!drawing.current || !startLngLat.current) return;
      const current: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      const src = map.getSource("selection") as GeoJSONSource | undefined;
      src?.setData(rectFeature(startLngLat.current, current));
      setAreaKm2(areaKm2Of(startLngLat.current, current));
    });

    map.on("mouseup", (e: MapMouseEvent) => {
      if (!drawing.current || !startLngLat.current) return;
      drawing.current = false;
      map.dragPan.enable();
      const end: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      const start = startLngLat.current;
      const minLon = Math.min(start[0], end[0]);
      const maxLon = Math.max(start[0], end[0]);
      const minLat = Math.min(start[1], end[1]);
      const maxLat = Math.max(start[1], end[1]);
      setBBox({ min_lon: minLon, min_lat: minLat, max_lon: maxLon, max_lat: maxLat });
      startLngLat.current = null;
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [setBBox]);

  // Phase 12 — render the selected GIS layer (NDVI/NDWI/NDBI/change masks) as
  // a georeferenced image overlay on top of the basemap.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const OVERLAY_ID = "gis-layer-overlay";

    if (map.getLayer(OVERLAY_ID)) map.removeLayer(OVERLAY_ID);
    if (map.getSource(OVERLAY_ID)) map.removeSource(OVERLAY_ID);

    if (layers && activeLayer) {
      map.addSource(OVERLAY_ID, {
        type: "image",
        url: layers.layers[activeLayer],
        coordinates: layers.bounds as [[number, number], [number, number], [number, number], [number, number]],
      });
      map.addLayer({
        id: OVERLAY_ID,
        type: "raster",
        source: OVERLAY_ID,
        paint: { "raster-opacity": 0.85 },
      });
    }
  }, [layers, activeLayer, mapLoaded]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      <div className="absolute left-3 top-3 max-w-[min(90%,320px)] rounded-xl border border-slate-700/80 bg-slate-950/90 px-3.5 py-3 text-xs text-slate-200 shadow-xl shadow-black/20 backdrop-blur-md sm:left-4 sm:top-4">
        <div className="mb-2 flex items-center gap-2"><span className="grid h-6 w-6 place-items-center rounded-lg bg-cyan-400/10 text-cyan-300" aria-hidden="true">◎</span><div><p className="font-semibold text-slate-100">Area of interest</p><p className="text-[10px] text-slate-500">Interactive map</p></div></div>
        <p className="text-[11px] leading-relaxed text-slate-400">Hold <kbd className="rounded border border-slate-600 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-200">Shift</kbd> and drag to select a region.</p>
        {bbox && (
          <p className="mt-2 border-t border-slate-800 pt-2 font-mono text-[10px] text-slate-400">
            {bbox.min_lat.toFixed(3)}, {bbox.min_lon.toFixed(3)} → {bbox.max_lat.toFixed(3)}, {bbox.max_lon.toFixed(3)}
          </p>
        )}
        {areaKm2 !== null && <p className="text-slate-400">~{areaKm2.toFixed(1)} km²</p>}
      </div>
    </div>
  );
}
