'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { BarChart3 } from 'lucide-react';

interface BenchmarkData {
  stops: number[];
  results: Array<{
    num_stops: number;
    qpso_cost: number;
    pso_cost: number;
    ga_cost: number;
    qpso_time_ms: number;
    pso_time_ms: number;
    ga_time_ms: number;
  }>;
}

interface ScalabilityChartProps {
  benchmarkData?: BenchmarkData;
}

export const ScalabilityChart: React.FC<ScalabilityChartProps> = ({ benchmarkData }) => {
  // Default fallback dataset if benchmark hasn't been fetched yet
  const defaultData = [
    { num_stops: '10 Stops', QPSO: 10816, PSO: 11766, GA: 13139 },
    { num_stops: '20 Stops', QPSO: 26272, PSO: 35232, GA: 35454 },
    { num_stops: '30 Stops', QPSO: 48920, PSO: 62100, GA: 64800 },
    { num_stops: '40 Stops', QPSO: 78400, PSO: 98500, GA: 104200 },
  ];

  const chartData = benchmarkData?.results
    ? benchmarkData.results.map((r) => ({
        num_stops: `${r.num_stops} Stops`,
        QPSO: Math.round(r.qpso_cost),
        PSO: Math.round(r.pso_cost),
        GA: Math.round(r.ga_cost),
      }))
    : defaultData;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900">Scalability Comparison Across Stop Sizes</h2>
        </div>
        <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-md">
          10 to 40 Delivery Stops
        </span>
      </div>

      <div className="h-64 w-full text-xs">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="num_stops" stroke="#64748b" tickLine={false} />
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
            <Bar dataKey="QPSO" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            <Bar dataKey="PSO" fill="#0284c7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="GA" fill="#059669" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
