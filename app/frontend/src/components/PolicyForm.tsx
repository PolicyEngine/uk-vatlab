'use client';

import { useState } from 'react';
import { PolicyReform } from '@/types';

interface PolicyFormProps {
  onSubmit: (reform: PolicyReform) => void;
  isLoading: boolean;
}

export default function PolicyForm({ onSubmit, isLoading }: PolicyFormProps) {
  const [reform, setReform] = useState<PolicyReform>({
    registration_threshold: 90000,
    taper_type: 'none',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(reform);
  };

  const handleTaperTypeChange = (type: PolicyReform['taper_type']) => {
    const updates: Partial<PolicyReform> = { taper_type: type };
    
    if (type === 'none') {
      updates.taper_start = undefined;
      updates.taper_end = undefined;
      updates.taper_rate = undefined;
    }
    
    setReform({ ...reform, ...updates });
  };

  return (
    <form onSubmit={handleSubmit} className="card p-6">
      <h2 className="text-2xl font-medium mb-6 heading-grad">Design your VAT reform</h2>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            Registration threshold
          </label>
          <div className="flex items-center space-x-2">
            <span className="font-mono">£</span>
            <input
              type="number"
              value={reform.registration_threshold}
              onChange={(e) => setReform({ ...reform, registration_threshold: parseInt(e.target.value) })}
              className="flex-1 px-3 py-2 font-mono focus:outline-none focus:ring-0 input"
              min="0"
              max="500000"
              step="1000"
            />
          </div>
          <p className="mt-1 text-xs text-subtle">
            Current baseline: £90,000 (2025-26)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Tapering option
          </label>
          <div className="space-y-3">
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                value="none"
                checked={reform.taper_type === 'none'}
                onChange={() => handleTaperTypeChange('none')}
                className="mt-1 mr-3 w-4 h-4 accent-white"
              />
              <div>
                <div className="font-medium">No taper</div>
                <div className="text-xs text-subtle">Full VAT liability above threshold</div>
              </div>
            </label>
            
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                value="custom"
                checked={reform.taper_type === 'custom'}
                onChange={() => handleTaperTypeChange('custom')}
                className="mt-1 mr-3 w-4 h-4 accent-white"
              />
              <div>
                <div className="font-medium">Custom taper</div>
                <div className="text-xs text-subtle">Define your own taper range</div>
              </div>
            </label>
          </div>
        </div>

        {reform.taper_type === 'custom' && (
          <div className="space-y-4 p-4 card">
            <div>
              <label className="block text-sm font-medium mb-2">
                Taper start
              </label>
              <div className="flex items-center space-x-2">
                <span className="font-mono">£</span>
                <input
                  type="number"
                  value={reform.taper_start || ''}
                  onChange={(e) => setReform({ ...reform, taper_start: parseInt(e.target.value) })}
                  className="flex-1 px-3 py-2 font-mono focus:outline-none focus:ring-0 input"
                  min="0"
                  max={reform.registration_threshold}
                  step="1000"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Taper end
              </label>
              <div className="flex items-center space-x-2">
                <span className="font-mono">£</span>
                <input
                  type="number"
                  value={reform.taper_end || ''}
                  onChange={(e) => setReform({ ...reform, taper_end: parseInt(e.target.value) })}
                  className="flex-1 px-3 py-2 font-mono focus:outline-none focus:ring-0 input"
                  min={reform.taper_start || reform.registration_threshold}
                  max="500000"
                  step="1000"
                />
              </div>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 font-medium btn-primary focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Analysing...' : 'Analyse reform'}
        </button>
      </div>
    </form>
  );
}
