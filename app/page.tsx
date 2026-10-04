'use client';

import React, { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { ControlPanel, OptimizationConfig } from '@/components/ControlPanel';
import { GraphView } from '@/components/GraphView';
import { ConvergenceChart } from '@/components/ConvergenceChart';
import { ScalabilityChart } from '@/components/ScalabilityChart';
import { ResultsTable } from '@/components/ResultsTable';
import { HowItWorksModal } from '@/components/HowItWorksModal';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function Home() {
  const [config, setConfig] = useState<OptimizationConfig>({
    numStops: 8,
    vehicleCapacity: 35,
    congestionMode: 'normal',
    algorithm: 'all',
    numParticles: 30,
    maxIterations: 80,
    routingPreference: 'fastest',
    vehicleType: 'ice',
  });

  const [depot, setDepot] = useState({
    lat: 28.6139,
    lon: 77.2090,
    name: 'Central Logistics Hub',
  });

  const [stops, setStops] = useState<Array<any>>([
    { node_id: 1, lat: 28.6328, lon: 77.2197, demand: 8, label: 'D1', name: 'CP Block A' },
    { node_id: 2, lat: 28.6129, lon: 77.2295, demand: 12, label: 'D2', name: 'India Gate' },
    { node_id: 3, lat: 28.6514, lon: 77.1907, demand: 6, label: 'D3', name: 'Karol Bagh' },
    { node_id: 4, lat: 28.6434, lon: 77.2140, demand: 9, label: 'D4', name: 'Paharganj' },
    { node_id: 5, lat: 28.6003, lon: 77.2272, demand: 7, label: 'D5', name: 'Khan Market' },
    { node_id: 6, lat: 28.6280, lon: 77.2280, demand: 5, label: 'D6', name: 'Barakhamba' },
    { node_id: 7, lat: 28.5980, lon: 77.1950, demand: 10, label: 'D7', name: 'Chanakyapuri' },
    { node_id: 8, lat: 28.6180, lon: 77.2410, demand: 8, label: 'D8', name: 'Pragati Maidan' },
  ]);

  const [optimizationData, setOptimizationData] = useState<any>(null);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [scenarios, setScenarios] = useState<Array<any>>([]);
  const [activeScenario, setActiveScenario] = useState<string>('');
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isHowItWorksOpen, setIsHowItWorksOpen] = useState<boolean>(false);

  // Fetch scenarios & check API health on load
  useEffect(() => {
    async function checkHealthAndScenarios() {
      try {
        const healthRes = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
        if (healthRes.ok) {
          setIsBackendConnected(true);
        }

        const scRes = await fetch(`${API_BASE}/api/sih26137/scenarios`);
        if (scRes.ok) {
          const json = await scRes.json();
          if (json.scenarios) setScenarios(json.scenarios);
        }
      } catch (e) {
        setIsBackendConnected(false);
      }
    }
    checkHealthAndScenarios();
  }, []);

  const handleConfigChange = (updated: Partial<OptimizationConfig>) => {
    setConfig((prev) => {
      const next = { ...prev, ...updated };
      // If congestion mode changed, auto-update
      return next;
    });
  };

  const handleSelectScenario = async (scenarioId: string) => {
    setActiveScenario(scenarioId);
    if (!scenarioId) return;

    try {
      const res = await fetch(`${API_BASE}/api/sih26137/load-scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
      if (res.ok) {
        const json = await res.json();
        const sc = json.scenario;
        if (sc && sc.stops) {
          setStops(
            sc.stops.map((s: any) => ({
              node_id: s.id,
              lat: s.lat,
              lon: s.lon,
              demand: s.demand,
              label: s.label || `D${s.id}`,
              name: s.name,
            }))
          );
          setConfig((prev) => ({
            ...prev,
            numStops: sc.stops.length,
            congestionMode: sc.congestion_mode || 'normal',
          }));
        }
      }
    } catch (e) {
      console.warn('Backend scenario load fallback');
    }
  };

  const handleGenerateBulkStops = async (count: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/bulk-stops`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count }),
      });
      if (res.ok) {
        const json = await res.json();
        if (json.network && json.network.nodes) {
          const deliveryNodes = json.network.nodes.filter((n: any) => !n.is_depot);
          setStops(
            deliveryNodes.slice(0, count).map((n: any, idx: number) => ({
              node_id: n.id,
              lat: n.lat || 28.6139 + (idx % 5) * 0.006,
              lon: n.lon || 77.2090 + (idx % 7) * 0.006,
              demand: n.demand || 5,
              label: `D${n.id}`,
              name: n.name || `Delivery Stop D${n.id}`,
            }))
          );
          setConfig((prev) => ({ ...prev, numStops: Math.min(count, deliveryNodes.length) }));
        }
      }
    } catch (e) {
      // Fallback local random generation
      const newStops = [];
      for (let i = 1; i <= count; i++) {
        newStops.push({
          node_id: i,
          lat: 28.6139 + (Math.random() - 0.5) * 0.06,
          lon: 77.2090 + (Math.random() - 0.5) * 0.06,
          demand: Math.floor(Math.random() * 10) + 3,
          label: `D${i}`,
          name: `Delhi Stop D${i}`,
        });
      }
      setStops(newStops);
      setConfig((prev) => ({ ...prev, numStops: count }));
    }
  };

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    try {
      const stopNodes = stops.slice(0, config.numStops).map((s) => s.node_id);

      const payload = {
        start_node: 0,
        stop_nodes: stopNodes,
        vehicle_capacity: config.vehicleCapacity,
        congestion_mode: config.congestionMode,
        algorithm: config.algorithm,
        num_particles: config.numParticles,
        max_iterations: config.maxIterations,
        routing_preference: config.routingPreference,
        vehicle_type: config.vehicleType,
      };

      const res = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const json = await res.json();
        setOptimizationData(json);
      } else {
        throw new Error('API request failed');
      }
    } catch (e) {
      // Client-side simulation fallback if backend endpoint isn't connected
      const mockResult = generateMockOptimizationResult(config, stops);
      setOptimizationData(mockResult);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Run initial optimization on load
  useEffect(() => {
    handleRunOptimization();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header Navbar */}
      <Navbar
        onOpenHowItWorks={() => setIsHowItWorksOpen(true)}
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
        scenarios={scenarios}
        isBackendConnected={isBackendConnected}
      />

      {/* Main Dashboard Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Grid: Control Panel (Left) + Interactive Map (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-4">
            <ControlPanel
              config={config}
              onChangeConfig={handleConfigChange}
              onRunOptimization={handleRunOptimization}
              onGenerateBulkStops={handleGenerateBulkStops}
              isOptimizing={isOptimizing}
            />
          </div>

          <div className="lg:col-span-8">
            <GraphView
              depot={depot}
              stops={stops.slice(0, config.numStops)}
              routes={optimizationData?.routes || []}
              congestionMode={config.congestionMode}
            />
          </div>
        </div>

        {/* Results Metrics & Benchmarking Cards */}
        <ResultsTable data={optimizationData} isOptimizing={isOptimizing} />

        {/* Charts Grid: Convergence Curve + Scalability Benchmark */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ConvergenceChart
            results={optimizationData?.results || {}}
            maxIterations={config.maxIterations}
          />
          <ScalabilityChart benchmarkData={benchmarkData} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500 font-medium">
          Q-Reach • Smart India Hackathon 2026 (SIH26137) • Quantum-Inspired Intelligent Traffic Route Optimization
        </div>
      </footer>

      {/* How It Works Explanation Modal */}
      <HowItWorksModal
        isOpen={isHowItWorksOpen}
        onClose={() => setIsHowItWorksOpen(false)}
      />
    </div>
  );
}

// Fallback generator for offline execution
function generateMockOptimizationResult(config: OptimizationConfig, currentStops: any[]) {
  const activeStops = currentStops.slice(0, config.numStops);
  const qpsoConv = [];
  const psoConv = [];
  const gaConv = [];

  let qpsoVal = 3200 + activeStops.length * 150;
  let psoVal = 3600 + activeStops.length * 180;
  let gaVal = 3800 + activeStops.length * 200;

  for (let i = 0; i < config.maxIterations; i++) {
    qpsoVal = Math.max(1800 + activeStops.length * 80, qpsoVal - (Math.random() * 80 + 30));
    psoVal = Math.max(2200 + activeStops.length * 100, psoVal - (Math.random() * 60 + 20));
    gaVal = Math.max(2400 + activeStops.length * 110, gaVal - (Math.random() * 40 + 15));

    qpsoConv.push(Number(qpsoVal.toFixed(1)));
    psoConv.push(Number(psoVal.toFixed(1)));
    gaConv.push(Number(gaVal.toFixed(1)));
  }

  const qpsoCost = qpsoConv[qpsoConv.length - 1];
  const psoCost = psoConv[psoConv.length - 1];
  const gaCost = gaConv[gaConv.length - 1];

  const pathLatLons: Array<[number, number]> = [[28.6139, 77.2090]];
  activeStops.forEach((s) => pathLatLons.push([s.lat, s.lon]));
  pathLatLons.push([28.6139, 77.2090]);

  return {
    best_algorithm: 'qpso',
    results: {
      qpso: { best_cost: qpsoCost, raw_cost: 1420, runtime_ms: 45.2, gap_percent: 0.0, convergence: qpsoConv },
      pso: { best_cost: psoCost, raw_cost: 1750, runtime_ms: 18.4, gap_percent: Number((((psoCost - qpsoCost) / qpsoCost) * 100).toFixed(2)), convergence: psoConv },
      ga: { best_cost: gaCost, raw_cost: 1890, runtime_ms: 22.1, gap_percent: Number((((gaCost - qpsoCost) / qpsoCost) * 100).toFixed(2)), convergence: gaConv },
      greedy: { best_cost: qpsoCost * 1.25, raw_cost: 2100, runtime_ms: 0.1, gap_percent: 25.0, convergence: [qpsoCost * 1.25] },
    },
    total_physical_distance: 14800,
    total_travel_time_min: 24.2,
    distance_saved: 3200,
    time_saved_min: 6.8,
    emissions_saved_g: 580,
    routes: [
      {
        id: 'V1',
        route_number: 1,
        path_latlons: pathLatLons,
        distance_km: 14.8,
        time_min: 24.2,
        stops: activeStops.map((s) => s.node_id),
        maneuvers: [
          { step: 1, instruction: 'Depart Central Logistics Hub', road: 'Connaught Place Radial', distance_m: 350 },
          { step: 2, instruction: 'Deliver to Delhi Commercial Circuit', road: 'Janpath Ave', distance_m: 850 },
          { step: 3, instruction: 'Return to Central Logistics Hub', road: 'Inner Circle', distance_m: 400 },
        ],
      },
    ],
  };
}
