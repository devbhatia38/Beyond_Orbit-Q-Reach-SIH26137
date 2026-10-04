'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Layers, MapPin, Navigation, Maximize2, RefreshCw } from 'lucide-react';

interface StopItem {
  node_id: number;
  lat: number;
  lon: number;
  demand: number;
  label?: string;
  name?: string;
}

interface ManeuverItem {
  step: number;
  instruction: string;
  icon?: string;
  road?: string;
  distance_m?: number;
}

interface VehicleRoute {
  id: string;
  route_number: number;
  path_latlons: Array<[number, number]>;
  distance_km: number;
  time_min: number;
  stops: number[];
  stops_data?: Array<{
    node_id: number;
    label: string;
    name: string;
    lat: number;
    lng: number;
    demand: number;
  }>;
  maneuvers?: ManeuverItem[];
}

interface GraphViewProps {
  depot: { lat: number; lon: number; name?: string };
  stops: StopItem[];
  routes: VehicleRoute[];
  congestionMode: string;
  onSelectStop?: (stop: StopItem) => void;
}

const ROUTE_COLORS = [
  '#4f46e5', // Indigo
  '#059669', // Emerald
  '#d97706', // Amber
  '#7c3aed', // Violet
  '#dc2626', // Red
  '#2563eb', // Blue
];

export const GraphView: React.FC<GraphViewProps> = ({
  depot,
  stops,
  routes,
  congestionMode,
  onSelectStop,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'maneuvers'>('map');
  const [selectedRouteIdx, setSelectedRouteIdx] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (typeof window === 'undefined' || !mapContainerRef.current) return;
      const L = (await import('leaflet')).default;

      if (!mapInstanceRef.current && mapContainerRef.current) {
        // Initialize Leaflet map with Central Delhi view
        const map = L.map(mapContainerRef.current, {
          center: [depot.lat || 28.6139, depot.lon || 77.2090],
          zoom: 13,
          zoomControl: false,
        });

        // Add Zoom Control at top right
        L.control.zoom({ position: 'topright' }).addTo(map);

        // OpenStreetMap Free Light Tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }).addTo(map);

        const layerGroup = L.layerGroup().addTo(map);
        mapInstanceRef.current = map;
        layerGroupRef.current = layerGroup;

        if (isMounted) setIsMapReady(true);
      }
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update markers & polylines on props change
  useEffect(() => {
    async function updateLayers() {
      if (!mapInstanceRef.current || !layerGroupRef.current) return;
      const L = (await import('leaflet')).default;
      const map = mapInstanceRef.current;
      const layerGroup = layerGroupRef.current;

      layerGroup.clearLayers();

      const bounds = L.latLngBounds([]);

      // 1. Central Logistics Hub (Depot Marker)
      const depotLat = depot.lat || 28.6139;
      const depotLon = depot.lon || 77.2090;
      bounds.extend([depotLat, depotLon]);

      const depotIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div style="background-color: #0f172a; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; border: 3px solid #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">
            🏠
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });

      const depotMarker = L.marker([depotLat, depotLon], { icon: depotIcon }).addTo(layerGroup);
      depotMarker.bindPopup(`
        <div style="font-family: inherit; padding: 4px;">
          <div style="font-weight: 700; font-size: 13px; color: #0f172a;">${depot.name || 'Central Logistics Hub'}</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Central Dispatch Center & Fleet Depot</div>
          <div style="font-size: 11px; font-weight: 600; color: #4f46e5; margin-top: 4px;">Start / End Point</div>
        </div>
      `);

      // 2. Delivery Stops Markers
      stops.forEach((stop, idx) => {
        const stopLat = stop.lat;
        const stopLon = stop.lon;
        if (!stopLat || !stopLon) return;

        bounds.extend([stopLat, stopLon]);

        const label = stop.label || `D${stop.node_id}`;
        const stopIcon = L.divIcon({
          className: 'custom-div-icon',
          html: `
            <div style="background-color: #4f46e5; color: white; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 11px; border: 2px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.15); text-align: center; white-space: nowrap;">
              ${label}
            </div>
          `,
          iconSize: [40, 22],
          iconAnchor: [20, 11],
        });

        const marker = L.marker([stopLat, stopLon], { icon: stopIcon }).addTo(layerGroup);
        marker.bindPopup(`
          <div style="font-family: inherit; padding: 4px;">
            <div style="font-weight: 700; font-size: 13px; color: #0f172a;">${stop.name || `Delivery Stop ${label}`}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Demand Payload: <b>${stop.demand} kg</b></div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">Lat: ${stopLat.toFixed(4)}, Lon: ${stopLon.toFixed(4)}</div>
          </div>
        `);
      });

      // 3. Vehicle Route Polylines
      routes.forEach((route, rIdx) => {
        const pathCoords = route.path_latlons;
        if (!pathCoords || pathCoords.length < 2) return;

        const color = ROUTE_COLORS[rIdx % ROUTE_COLORS.length];

        const polyline = L.polyline(pathCoords, {
          color: color,
          weight: 4,
          opacity: 0.85,
          dashArray: congestionMode === 'rush_hour' ? '8, 6' : undefined,
        }).addTo(layerGroup);

        pathCoords.forEach(([lat, lon]) => bounds.extend([lat, lon]));

        polyline.bindPopup(`
          <div style="font-family: inherit; padding: 4px;">
            <div style="font-weight: 700; font-size: 13px; color: ${color};">Vehicle Route #${route.route_number || rIdx + 1}</div>
            <div style="font-size: 11px; color: #334155; margin-top: 4px;">Distance: <b>${route.distance_km} km</b></div>
            <div style="font-size: 11px; color: #334155;">Estimated Time: <b>${route.time_min} min</b></div>
            <div style="font-size: 11px; color: #334155;">Stops Visited: <b>${route.stops ? route.stops.length : 0}</b></div>
          </div>
        `);
      });

      // Fit bounds with padding if valid
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
      }
    }

    if (isMapReady) {
      updateLayers();
    }
  }, [isMapReady, depot, stops, routes, congestionMode]);

  const handleRecenter = () => {
    if (mapInstanceRef.current && (depot.lat || depot.lon)) {
      mapInstanceRef.current.setView([depot.lat || 28.6139, depot.lon || 77.2090], 13);
    }
  };

  const selectedRoute = routes[selectedRouteIdx] || routes[0];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col h-[520px]">
      {/* Map Header Tabs & Controls */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('map')}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'map'
                ? 'bg-white text-indigo-600 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            🗺️ Interactive Route Map
          </button>
          <button
            onClick={() => setActiveTab('maneuvers')}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'maneuvers'
                ? 'bg-white text-indigo-600 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            🧭 Turn-By-Turn Guidance
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-500 hidden sm:inline">
            Stops: <b className="text-slate-800">{stops.length}</b>
          </span>
          <button
            onClick={handleRecenter}
            className="p-1.5 bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 rounded-md shadow-2xs cursor-pointer"
            title="Recenter Map"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Map Canvas / Turn-by-turn Content */}
      <div className="relative flex-1 w-full h-full">
        {activeTab === 'map' ? (
          <div className="w-full h-full" ref={mapContainerRef}>
            {/* Overlay legend */}
            <div className="absolute bottom-3 left-3 z-10 bg-white/95 backdrop-blur-xs border border-slate-200 p-2.5 rounded-lg shadow-sm text-xs space-y-1">
              <div className="font-semibold text-slate-800 border-b border-slate-100 pb-1 mb-1">
                Route Legend
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full bg-slate-900 border border-white"></span>
                <span className="text-slate-600">Logistics Hub (Depot)</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-md bg-indigo-600"></span>
                <span className="text-slate-600">Delivery Stops</span>
              </div>
              {routes.map((r, i) => (
                <div key={r.id || i} className="flex items-center space-x-2">
                  <span
                    className="w-4 h-1 rounded-full"
                    style={{ backgroundColor: ROUTE_COLORS[i % ROUTE_COLORS.length] }}
                  ></span>
                  <span className="text-slate-700 font-medium">
                    Vehicle #{r.route_number || i + 1} ({r.distance_km} km)
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full h-full bg-slate-50 p-4 overflow-y-auto space-y-3">
            {routes.length > 1 && (
              <div className="flex space-x-2 border-b border-slate-200 pb-2">
                {routes.map((r, idx) => (
                  <button
                    key={r.id || idx}
                    onClick={() => setSelectedRouteIdx(idx)}
                    className={`px-3 py-1 rounded-md text-xs font-semibold cursor-pointer ${
                      selectedRouteIdx === idx
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Vehicle #{r.route_number || idx + 1}
                  </button>
                ))}
              </div>
            )}

            {selectedRoute && selectedRoute.maneuvers && selectedRoute.maneuvers.length > 0 ? (
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-700 mb-2">
                  Navigating Route #{selectedRoute.route_number || 1} • {selectedRoute.distance_km} km ({selectedRoute.time_min} mins)
                </div>
                {selectedRoute.maneuvers.map((m, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-3 bg-white border border-slate-200 rounded-lg p-2.5 shadow-2xs"
                  >
                    <div className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                      {m.step}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900">{m.instruction}</div>
                      {m.road && (
                        <div className="text-[11px] text-slate-500">
                          Road: <span className="font-medium text-slate-700">{m.road}</span> • Distance: {m.distance_m || 0}m
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-2">
                <Navigation className="w-8 h-8 text-slate-300" />
                <p className="text-xs font-medium">Run optimization to generate turn-by-turn guidance</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
