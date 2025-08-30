'use client';

import { PolicyAnalysisResult } from '@/types';
import AnimatedNumber from './AnimatedNumber';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface ResultsDisplayProps {
  results: PolicyAnalysisResult;
}


export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  const formatCurrency = (value: number) => {
    if (Math.abs(value) >= 1000) {
      return `£${(value / 1000).toFixed(1)}bn`;
    }
    return `£${value.toFixed(0)}m`;
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString();
  };

  return (
    <div className="space-y-8">
      <div className="border-4 border-black p-6">
        <h2 className="text-2xl font-black uppercase mb-4">Impact summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="border-2 border-black p-4">
            <div className="text-xs font-bold uppercase">Total revenue impact</div>
            <div className="text-2xl font-black">
              <AnimatedNumber 
                value={results.total_impact} 
                format={formatCurrency}
              />
            </div>
            <div className="text-xs mt-1">Over budget window</div>
          </div>
          
          <div className="border-2 border-black p-4">
            <div className="text-xs font-bold uppercase">Registration threshold</div>
            <div className="text-2xl font-black">
              <AnimatedNumber 
                value={results.reform_summary.registration_threshold} 
                format={(v) => `£${v.toLocaleString()}`}
              />
            </div>
            <div className="text-xs mt-1">
              {results.reform_summary.taper_type !== 'none' ? `With ${results.reform_summary.taper_type} taper` : 'No taper'}
            </div>
          </div>
          
          <div className="border-2 border-black p-4">
            <div className="text-xs font-bold uppercase">Firms affected</div>
            <div className="text-2xl font-black">
              <AnimatedNumber 
                value={results.yearly_impacts.reduce((sum, y) => sum + y.firms_affected, 0)} 
                format={formatNumber}
              />
            </div>
            <div className="text-xs mt-1">Total across all years</div>
          </div>
        </div>
      </div>

      <div className="border-4 border-black p-6">
        <h3 className="text-xl font-black uppercase mb-4">Revenue impact by year</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={results.yearly_impacts}>
            <CartesianGrid stroke="#000" strokeDasharray="0" />
            <XAxis dataKey="year" stroke="#000" />
            <YAxis tickFormatter={(v) => `£${v}m`} stroke="#000" />
            <Tooltip 
              formatter={(v: any) => `£${v}m`}
              contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="revenue_impact" 
              stroke="#000" 
              strokeWidth={3}
              name="Revenue impact (£m)"
              dot={{ fill: '#000', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
        
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b-2 border-black">
                <th className="text-left py-2 font-bold uppercase">Year</th>
                <th className="text-right py-2 font-bold uppercase">Baseline (£bn)</th>
                <th className="text-right py-2 font-bold uppercase">Reform (£bn)</th>
                <th className="text-right py-2 font-bold uppercase">Impact (£m)</th>
                <th className="text-right py-2 font-bold uppercase">Firms affected</th>
              </tr>
            </thead>
            <tbody>
              {results.yearly_impacts.map((year) => (
                <tr key={year.year} className="border-b border-black">
                  <td className="py-2">{year.year}</td>
                  <td className="text-right font-mono">
                    <AnimatedNumber value={year.baseline_revenue} format={(v) => v.toFixed(2)} />
                  </td>
                  <td className="text-right font-mono">
                    <AnimatedNumber value={year.reform_revenue} format={(v) => v.toFixed(2)} />
                  </td>
                  <td className="text-right font-bold font-mono">
                    {year.revenue_impact >= 0 ? '+' : ''}
                    <AnimatedNumber value={year.revenue_impact} format={(v) => v.toFixed(0)} />
                  </td>
                  <td className="text-right font-mono">
                    <AnimatedNumber value={year.firms_affected} format={formatNumber} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="border-4 border-black p-6">
        <h3 className="text-xl font-black uppercase mb-4">Impact by revenue band</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={results.revenue_band_impacts.filter(b => b.revenue_impact !== 0)}>
            <CartesianGrid stroke="#000" strokeDasharray="0" />
            <XAxis 
              dataKey="band" 
              angle={-45}
              textAnchor="end"
              height={100}
              stroke="#000"
            />
            <YAxis tickFormatter={(v) => `£${v}m`} stroke="#000" />
            <Tooltip 
              formatter={(v: any) => `£${v}m`}
              contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }}
            />
            <Bar dataKey="revenue_impact" name="Impact (£m)" fill="#000">
              {results.revenue_band_impacts.filter(b => b.revenue_impact !== 0).map((entry, index) => (
                <Cell key={`cell-${index}`} fill="#000" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
          
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b-2 border-black">
                  <th className="text-left py-2 font-bold uppercase">Revenue band</th>
                  <th className="text-right py-2 font-bold uppercase">Baseline VAT (£bn)</th>
                  <th className="text-right py-2 font-bold uppercase">Reform VAT (£bn)</th>
                  <th className="text-right py-2 font-bold uppercase">Impact (£m)</th>
                  <th className="text-right py-2 font-bold uppercase">Firms affected</th>
                </tr>
              </thead>
              <tbody>
                {results.revenue_band_impacts.filter(b => b.revenue_impact !== 0).map((band) => (
                  <tr key={band.band} className="border-b border-black">
                    <td className="py-2">{band.band}</td>
                    <td className="text-right font-mono">
                      <AnimatedNumber value={band.baseline_vat} format={(v) => v.toFixed(3)} />
                    </td>
                    <td className="text-right font-mono">
                      <AnimatedNumber value={band.reform_vat} format={(v) => v.toFixed(3)} />
                    </td>
                    <td className="text-right font-bold font-mono">
                      {band.revenue_impact >= 0 ? '+' : ''}
                      <AnimatedNumber value={band.revenue_impact} format={(v) => v.toFixed(1)} />
                    </td>
                    <td className="text-right font-mono">
                      <AnimatedNumber value={band.firms_affected} format={formatNumber} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      </div>
    </div>
  );
}