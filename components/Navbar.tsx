'use client';

import React from 'react';
import { Route, Zap, Shield, HelpCircle, Layers, Activity } from 'lucide-react';

interface NavbarProps {
  onOpenHowItWorks: () => void;
  activeScenario: string;
  onSelectScenario: (scenarioId: string) => void;
  scenarios: Array<{ id: string; title: string }>;
  isBackendConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenHowItWorks,
  activeScenario,
  onSelectScenario,
  scenarios,
  isBackendConnected,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs font-semibold">
              <Route className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">Q-Reach</span>
                <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-md">
                  SIH26137
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium hidden sm:block">
                Quantum-Inspired Traffic Route Optimization
              </p>
            </div>
          </div>

          {/* Scenario Selector & Status */}
          <div className="flex items-center space-x-3">
            {scenarios.length > 0 && (
              <div className="hidden md:flex items-center space-x-2 bg-slate-50 border border-slate-200 rounded-lg p-1">
                <Layers className="w-4 h-4 text-slate-500 ml-2" />
                <select
                  value={activeScenario}
                  onChange={(e) => onSelectScenario(e.target.value)}
                  className="bg-transparent text-xs font-medium text-slate-700 pr-4 py-1 focus:outline-hidden cursor-pointer"
                >
                  <option value="">-- Custom Network --</option>
                  {scenarios.map((sc) => (
                    <option key={sc.id} value={sc.id}>
                      {sc.title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Backend Connection Badge */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                isBackendConnected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>{isBackendConnected ? 'Engine Ready' : 'Simulated'}</span>
            </div>

            {/* How It Works Button */}
            <button
              onClick={onOpenHowItWorks}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 hover:text-indigo-600 transition-colors shadow-2xs cursor-pointer"
            >
              <HelpCircle className="w-4 h-4 text-slate-500" />
              <span className="hidden sm:inline">How It Works</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
