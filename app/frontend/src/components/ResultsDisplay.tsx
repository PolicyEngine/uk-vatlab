'use client';

import { PolicyAnalysisResult } from '@/types';
import AnimatedNumber from './AnimatedNumber';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
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
      <div className="border-2 border-black p-6">
        <h2 className="text-2xl font-medium mb-4">Impact summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="border border-black p-4">
            <div className="text-sm font-medium">Total revenue impact</div>
            <div className="text-2xl font-semibold">
              <AnimatedNumber 
                value={results.total_impact} 
                format={formatCurrency}
              />
            </div>
            <div className="text-xs mt-1">Over budget window</div>
          </div>
          
          <div className="border border-black p-4">
            <div className="text-sm font-medium">Registration threshold</div>
            <div className="text-2xl font-semibold">
              <AnimatedNumber 
                value={results.reform_summary.registration_threshold} 
                format={(v) => `£${v.toLocaleString()}`}
              />
            </div>
            <div className="text-xs mt-1">
              {results.reform_summary.taper_type !== 'none' ? `With ${results.reform_summary.taper_type} taper` : 'No taper'}
            </div>
          </div>
          
          <div className="border border-black p-4">
            <div className="text-sm font-medium">Firms affected</div>
            <div className="text-2xl font-semibold">
              <AnimatedNumber 
                value={results.yearly_impacts.reduce((sum, y) => sum + y.firms_affected, 0)} 
                format={formatNumber}
              />
            </div>
            <div className="text-xs mt-1">Total across all years</div>
          </div>
        </div>
      </div>

      <div className="border-2 border-black p-6">
        <h3 className="text-xl font-medium mb-4">Revenue impact by year</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={results.yearly_impacts} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid 
              stroke="#e0e0e0" 
              strokeDasharray="0" 
              vertical={false}
            />
            <XAxis 
              dataKey="year" 
              stroke="#000" 
              tick={{ fill: '#000' }}
              axisLine={{ stroke: '#000', strokeWidth: 1 }}
            />
            <YAxis 
              tickFormatter={(v) => `£${v}m`} 
              stroke="#000" 
              tick={{ fill: '#000' }}
              axisLine={{ stroke: '#000', strokeWidth: 1 }}
              domain={['dataMin', 'dataMax']}
              ticks={(() => {
                const min = Math.min(...results.yearly_impacts.map(d => d.revenue_impact));
                const max = Math.max(...results.yearly_impacts.map(d => d.revenue_impact));
                const range = max - min;
                const step = Math.ceil(range / 5 / 100) * 100;
                const ticks = [];
                for (let i = Math.floor(min / step) * step; i <= Math.ceil(max / step) * step; i += step) {
                  ticks.push(i);
                }
                if (!ticks.includes(0) && min < 0 && max > 0) ticks.push(0);
                return ticks.sort((a, b) => a - b);
              })()}
            />
            <Tooltip 
              formatter={(v: any) => `£${v}m`}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #000' }}
            />
            <ReferenceLine y={0} stroke="#000" strokeWidth={1.5} />
            <Bar 
              dataKey="revenue_impact" 
              fill="#000" 
            />
          </BarChart>
        </ResponsiveContainer>
        
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-black">
                <th className="text-left py-2 font-medium">Year</th>
                <th className="text-right py-2 font-medium">Baseline (£bn)</th>
                <th className="text-right py-2 font-medium">Reform (£bn)</th>
                <th className="text-right py-2 font-medium">Impact (£m)</th>
                <th className="text-right py-2 font-medium">Firms affected</th>
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
                  <td className="text-right font-medium font-mono">
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

      <div className="border-2 border-black p-6">
        <h3 className="text-xl font-medium mb-4">Impact by revenue band</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={results.revenue_band_impacts} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
            <CartesianGrid 
              stroke="#e0e0e0" 
              strokeDasharray="0" 
              vertical={false}
            />
            <XAxis 
              dataKey="band" 
              angle={-45}
              textAnchor="end"
              height={100}
              stroke="#000"
              tick={{ fill: '#000' }}
              axisLine={{ stroke: '#000', strokeWidth: 1 }}
            />
            <YAxis 
              tickFormatter={(v) => `£${v}m`} 
              stroke="#000" 
              tick={{ fill: '#000' }}
              axisLine={{ stroke: '#000', strokeWidth: 1 }}
              domain={['dataMin', 'dataMax']}
              ticks={(() => {
                const values = results.revenue_band_impacts.map(d => d.revenue_impact);
                const min = Math.min(...values);
                const max = Math.max(...values);
                const range = max - min;
                const step = range > 0 ? Math.ceil(range / 5 / 10) * 10 : 10;
                const ticks = [];
                for (let i = Math.floor(min / step) * step; i <= Math.ceil(max / step) * step; i += step) {
                  ticks.push(i);
                }
                if (!ticks.includes(0) && min < 0 && max > 0) ticks.push(0);
                return ticks.sort((a, b) => a - b);
              })()}
            />
            <Tooltip 
              formatter={(v: any) => `£${v}m`}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #000' }}
            />
            <ReferenceLine y={0} stroke="#000" strokeWidth={1.5} />
            <Bar dataKey="revenue_impact" fill="#000" />
          </BarChart>
        </ResponsiveContainer>
          
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-black">
                  <th className="text-left py-2 font-medium">Revenue band</th>
                  <th className="text-right py-2 font-medium">Baseline VAT (£bn)</th>
                  <th className="text-right py-2 font-medium">Reform VAT (£bn)</th>
                  <th className="text-right py-2 font-medium">Impact (£m)</th>
                  <th className="text-right py-2 font-medium">Firms affected</th>
                </tr>
              </thead>
              <tbody>
                {results.revenue_band_impacts.map((band) => (
                  <tr key={band.band} className="border-b border-black">
                    <td className="py-2">{band.band}</td>
                    <td className="text-right font-mono">
                      <AnimatedNumber value={band.baseline_vat} format={(v) => v.toFixed(3)} />
                    </td>
                    <td className="text-right font-mono">
                      <AnimatedNumber value={band.reform_vat} format={(v) => v.toFixed(3)} />
                    </td>
                    <td className="text-right font-medium font-mono">
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