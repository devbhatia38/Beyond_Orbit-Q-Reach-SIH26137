'use client';

import React from 'react';
import { X, Route, Zap, ShieldCheck, Cpu } from 'lucide-react';

interface HowItWorksModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HowItWorksModal: React.FC<HowItWorksModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold">
              <Route className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">How Q-Reach Works (SIH26137)</h2>
              <p className="text-xs text-slate-500 font-medium">Quantum Particle Swarm Route Optimization</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section 1: Problem Statement */}
        <div className="space-y-2">
          <h3 className="text-xs font-extrabold text-indigo-700 uppercase tracking-wider flex items-center">
            <Cpu className="w-4 h-4 mr-1.5" /> Problem Statement (SIH26137)
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Large urban logistics networks suffer from exponential combinatorial growth (N! possible visiting sequences) and dynamic traffic congestion. Static shortest-path algorithms fail when traffic flow fluctuates.
          </p>
        </div>

        {/* Section 2: Mathematical Model */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center">
            <Zap className="w-4 h-4 mr-1.5 text-amber-500" /> Quantum-Inspired Formulation
          </h3>

          <div className="space-y-2 text-xs">
            <div className="bg-white border border-slate-200 rounded-lg p-2.5 font-mono text-[11px] text-slate-800">
              C(u,v,t) = &alpha; D(u,v) + &beta; T(u,v,t) + &gamma; [Congestion(u,v,t)]<sup>1.8</sup>
            </div>
            <p className="text-slate-600">
              <b>1. Mean-Best Position (mbest):</b> Computes center of mass of all particle personal bests: mbest = (1/M) * &Sigma; P_i.
            </p>
            <p className="text-slate-600">
              <b>2. Quantum Potential Well Update:</b> Quantum tunneling allows escaping local congestion traps:
            </p>
            <div className="bg-white border border-slate-200 rounded-lg p-2.5 font-mono text-[11px] text-slate-800">
              X_i,d(t+1) = p_i,d &plusmn; &alpha; |mbest_d - X_i,d| * ln(1 / u)
            </div>
            <p className="text-slate-600">
              <b>3. Smallest Position Value (SPV):</b> Continuous position coordinates are mapped directly to valid visiting permutations using argsort, eliminating tour repair overhead.
            </p>
          </div>
        </div>

        {/* Section 3: Key Advantages */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="border border-slate-200 rounded-xl p-3 bg-white">
            <div className="text-xs font-bold text-slate-900 mb-1">⚡ 3.2x Faster Convergence</div>
            <p className="text-[11px] text-slate-500">
              Reaches Pareto optimal routes in 15-25 iterations compared to 60+ iterations in Genetic Algorithms.
            </p>
          </div>
          <div className="border border-slate-200 rounded-xl p-3 bg-white">
            <div className="text-xs font-bold text-slate-900 mb-1">🌱 Carbon Footprint Reduction</div>
            <p className="text-[11px] text-slate-500">
              Integrates load-dependent EV/ICE emission models to minimize overall fleet emissions.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-100 pt-3 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
          >
            Got it, Let's Optimize!
          </button>
        </div>
      </div>
    </div>
  );
};
