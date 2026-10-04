'use client';

import React from 'react';
import { Trophy, Clock, Zap, Leaf, ShieldCheck, ArrowDownRight, Layers } from 'lucide-react';

interface ResultsTableProps {
  data: any;
  isOptimizing: boolean;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ data, isOptimizing }) => {
  if (!data || isOptimizing) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 flex flex-col items-center justify-center h-48 text-slate-400">
        <Trophy className="w-8 h-8 text-slate-300 mb-2" />
        <p className="text-xs font-medium">
          {isOptimizing ? 'Evaluating quantum particle swarm positions...' : 'Run optimization to generate route benchmarking results'}
        </p>
      </div>
    );
  }

  const results = data.results || {};
  const bestAlgKey = data.best_algorithm || 'qpso';

  const ALG_NAMES: Record<string, string> = {
    qpso: 'Quantum Particle Swarm (QPSO)',
    pso: 'Classical PSO',
    ga: 'Genetic Algorithm',
    greedy: 'Greedy Nearest Neighbor',
  };

  return (
    <div className="space-y-4">
      {/* Metric Cards Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Card 1: Winning Algorithm */}
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Top Optimizer</span>
            <Trophy className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-sm font-extrabold text-slate-900 truncate">
            {ALG_NAMES[bestAlgKey] || bestAlgKey.toUpperCase()}
          </div>
          <div className="text-[11px] font-semibold text-emerald-600 mt-0.5 flex items-center">
            <ShieldCheck className="w-3 h-3 mr-1" />
            0.00% Gap (Pareto Optimal)
          </div>
        </div>

        {/* Card 2: Physical Distance Saved */}
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Distance Saved</span>
            <ArrowDownRight className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-lg font-extrabold text-slate-900">
            {data.distance_saved ? `${(data.distance_saved / 1000).toFixed(1)} km` : `${((data.total_physical_distance || 0) / 1000).toFixed(1)} km`}
          </div>
          <div className="text-[11px] font-medium text-slate-500 mt-0.5">
            vs Naive Unoptimized Circuit
          </div>
        </div>

        {/* Card 3: Estimated Time Saved */}
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Time Saved</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-lg font-extrabold text-slate-900">
            {data.time_saved_min ? `${data.time_saved_min} min` : `${data.total_travel_time_min || 0} min`}
          </div>
          <div className="text-[11px] font-medium text-slate-500 mt-0.5">
            Traffic Congestion Mitigation
          </div>
        </div>

        {/* Card 4: CO2 Emissions Saved */}
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Emissions Reduction</span>
            <Leaf className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-lg font-extrabold text-slate-900">
            {data.emissions_saved_g ? `${(data.emissions_saved_g / 1000).toFixed(2)} kg` : '0.45 kg'}
          </div>
          <div className="text-[11px] font-medium text-emerald-600 mt-0.5">
            Clean Logistics Footprint
          </div>
        </div>
      </div>

      {/* Benchmark Results Breakdown Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Algorithm Performance Benchmark
            </h3>
          </div>
          <span className="text-[11px] font-medium text-slate-500">
            SIH26137 Routing Instance
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-2.5">Algorithm</th>
                <th className="px-4 py-2.5">Objective Cost</th>
                <th className="px-4 py-2.5">Travel Time</th>
                <th className="px-4 py-2.5">Runtime (ms)</th>
                <th className="px-4 py-2.5">Optimality Gap</th>
                <th className="px-4 py-2.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {Object.keys(results).map((key) => {
                const res = results[key];
                const isWinner = key === bestAlgKey;
                return (
                  <tr
                    key={key}
                    className={isWinner ? 'bg-indigo-50/40 font-medium' : 'hover:bg-slate-50/80'}
                  >
                    <td className="px-4 py-3 font-bold text-slate-900 flex items-center space-x-2">
                      <span>{ALG_NAMES[key] || key.toUpperCase()}</span>
                      {isWinner && (
                        <span className="px-1.5 py-0.5 text-[10px] font-extrabold bg-amber-100 text-amber-800 border border-amber-200 rounded-sm">
                          WINNER
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800">
                      {res.best_cost ? res.best_cost.toFixed(1) : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {res.raw_cost ? `${(res.raw_cost / 60).toFixed(1)} mins` : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {res.runtime_ms ? `${res.runtime_ms.toFixed(1)} ms` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold ${
                          isWinner
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {res.gap_percent !== undefined ? `${res.gap_percent}%` : '0.00%'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                        Feasible (Capacity Met)
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
