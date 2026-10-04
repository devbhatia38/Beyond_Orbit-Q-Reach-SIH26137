'use client';

import React from 'react';
import { Play, RefreshCw, Zap, Sliders, Truck, ShieldAlert, Sparkles, Navigation } from 'lucide-react';

export interface OptimizationConfig {
  numStops: number;
  vehicleCapacity: number;
  congestionMode: 'normal' | 'rush_hour';
  algorithm: string;
  numParticles: number;
  maxIterations: number;
  routingPreference: 'fastest' | 'balanced' | 'greenest';
  vehicleType: 'ice' | 'ev';
}

interface ControlPanelProps {
  config: OptimizationConfig;
  onChangeConfig: (updated: Partial<OptimizationConfig>) => void;
  onRunOptimization: () => void;
  onGenerateBulkStops: (count: number) => void;
  isOptimizing: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  config,
  onChangeConfig,
  onRunOptimization,
  onGenerateBulkStops,
  isOptimizing,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900">Optimization Parameters</h2>
        </div>
        <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-md">
          QPSO Metaheuristic
        </span>
      </div>

      {/* Traffic Congestion Mode Toggle */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
          Traffic Congestion Environment
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onChangeConfig({ congestionMode: 'normal' })}
            className={`flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
              config.congestionMode === 'normal'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300 ring-2 ring-emerald-100'
                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Normal Traffic Flow</span>
          </button>
          <button
            type="button"
            onClick={() => onChangeConfig({ congestionMode: 'rush_hour' })}
            className={`flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
              config.congestionMode === 'rush_hour'
                ? 'bg-amber-50 text-amber-700 border-amber-300 ring-2 ring-amber-100'
                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span>Rush Hour Congestion</span>
          </button>
        </div>
      </div>

      {/* Routing Preference & Vehicle Type */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Routing Objective
          </label>
          <select
            value={config.routingPreference}
            onChange={(e) => onChangeConfig({ routingPreference: e.target.value as any })}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          >
            <option value="fastest">⚡ Fastest Travel Time</option>
            <option value="balanced">⚖️ Balanced (Time & CO2)</option>
            <option value="greenest">🌱 Greenest (Min Emissions)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Fleet Vehicle Type
          </label>
          <select
            value={config.vehicleType}
            onChange={(e) => onChangeConfig({ vehicleType: e.target.value as any })}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          >
            <option value="ice">🚚 Internal Combustion (ICE)</option>
            <option value="ev">⚡ Electric Vehicle (EV)</option>
          </select>
        </div>
      </div>

      {/* Stop Count & Vehicle Capacity */}
      <div className="space-y-3 pt-1">
        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
            <span>Delivery Stops ({config.numStops})</span>
            <div className="flex space-x-1">
              {[8, 12, 20].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => onGenerateBulkStops(count)}
                  className="px-1.5 py-0.5 text-[10px] bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-600 border border-slate-200 rounded-xs cursor-pointer font-medium"
                >
                  +{count} Stops
                </button>
              ))}
            </div>
          </div>
          <input
            type="range"
            min={4}
            max={30}
            value={config.numStops}
            onChange={(e) => onChangeConfig({ numStops: parseInt(e.target.value) })}
            className="w-full accent-indigo-600 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
            <span>Vehicle Capacity ({config.vehicleCapacity} kg)</span>
          </div>
          <input
            type="range"
            min={15}
            max={100}
            step={5}
            value={config.vehicleCapacity}
            onChange={(e) => onChangeConfig({ vehicleCapacity: parseInt(e.target.value) })}
            className="w-full accent-indigo-600 cursor-pointer"
          />
        </div>
      </div>

      {/* QPSO Algorithm Parameters */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-3">
        <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block">
          Quantum Swarm Hyperparameters
        </span>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Particles ({config.numParticles})
            </label>
            <input
              type="range"
              min={15}
              max={60}
              step={5}
              value={config.numParticles}
              onChange={(e) => onChangeConfig({ numParticles: parseInt(e.target.value) })}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Iterations ({config.maxIterations})
            </label>
            <input
              type="range"
              min={30}
              max={150}
              step={10}
              value={config.maxIterations}
              onChange={(e) => onChangeConfig({ maxIterations: parseInt(e.target.value) })}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            Algorithm Mode
          </label>
          <select
            value={config.algorithm}
            onChange={(e) => onChangeConfig({ algorithm: e.target.value })}
            className="w-full bg-white border border-slate-200 rounded-md px-2.5 py-1.5 text-xs font-medium text-slate-800"
          >
            <option value="all">⚡ Benchmark All (QPSO vs PSO vs GA vs Greedy)</option>
            <option value="qpso">⚛️ QPSO (Quantum Particle Swarm)</option>
            <option value="pso">🕊️ Classical PSO</option>
            <option value="ga">🧬 Genetic Algorithm</option>
            <option value="greedy">📍 Greedy Nearest Neighbor</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <button
        type="button"
        disabled={isOptimizing}
        onClick={onRunOptimization}
        className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white py-3 px-4 rounded-xl font-semibold text-sm transition-all shadow-sm hover:shadow-md active:scale-[0.99] disabled:opacity-60 cursor-pointer"
      >
        {isOptimizing ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin text-white" />
            <span>Computing QPSO Quantum Wavefront...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4 text-indigo-200" />
            <span>Optimize Routes with QPSO</span>
          </>
        )}
      </button>
    </div>
  );
};
