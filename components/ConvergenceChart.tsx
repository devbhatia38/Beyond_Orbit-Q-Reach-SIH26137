'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Activity } from 'lucide-react';

interface ConvergenceChartProps {
  results: Record<string, any>;
  maxIterations: number;
}

export const ConvergenceChart: React.FC<ConvergenceChartProps> = ({
  results,
  maxIterations,
}) => {
  if (!results || Object.keys(results).length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 flex flex-col items-center justify-center h-64 text-slate-400">
        <Activity className="w-8 h-8 text-slate-300 mb-2" />
        <p className="text-xs font-medium">Run optimization to view convergence curves</p>
      </div>
    );
  }

  // Construct iteration data points for Recharts
  const data = [];
  const keys = Object.keys(results);

  const iterationsCount = Math.max(
    ...keys.map((k) => (results[k].convergence ? results[k].convergence.length : 0)),
    maxIterations
  );

  for (let i = 0; i < iterationsCount; i++) {
    const point: Record<string, any> = { iteration: i + 1 };
    keys.forEach((key) => {
      const conv = results[key].convergence;
      if (conv && conv.length > 0) {
        point[key] = conv[Math.min(i, conv.length - 1)];
      }
    });
    data.push(point);
  }

  const ALG_COLORS: Record<string, string> = {
    qpso: '#4f46e5',   // Indigo
    pso: '#0284c7',    // Sky Blue
    ga: '#059669',     // Emerald
    greedy: '#d97706', // Amber
  };

  const ALG_NAMES: Record<string, string> = {
    qpso: 'QPSO (Quantum Swarm)',
    pso: 'Classical PSO',
    ga: 'Genetic Algorithm',
    greedy: 'Greedy Nearest Neighbor',
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900">Optimization Convergence Profile</h2>
        </div>
        <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-md">
          Objective Cost vs Iterations
        </span>
      </div>

      <div className="h-64 w-full text-xs">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="iteration"
              stroke="#64748b"
              tickLine={false}
              label={{ value: 'Iteration', position: 'insideBottomRight', offset: -5 }}
            />
            <YAxis stroke="#64748b" tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#cbd5e1',
                borderRadius: '8px',
                fontSize: '11px',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
            {keys.map((key) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={ALG_NAMES[key] || key.toUpperCase()}
                stroke={ALG_COLORS[key] || '#6366f1'}
                strokeWidth={key === 'qpso' ? 3 : 2}
                dot={false}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
