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
    
    if (type === 'moderate') {
      updates.taper_start = Math.max(65000, reform.registration_threshold - 25000);
      updates.taper_end = reform.registration_threshold + 20000;
    } else if (type === 'aggressive') {
      updates.taper_start = Math.max(50000, reform.registration_threshold - 35000);
      updates.taper_end = reform.registration_threshold + 10000;
    } else if (type === 'none') {
      updates.taper_start = undefined;
      updates.taper_end = undefined;
      updates.taper_rate = undefined;
    }
    
    setReform({ ...reform, ...updates });
  };

  return (
    <form onSubmit={handleSubmit} className="border-2 border-black p-6">
      <h2 className="text-2xl font-medium mb-6">Design your VAT reform</h2>
      
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
              className="flex-1 px-3 py-2 border border-black font-mono focus:outline-none focus:ring-0"
              min="0"
              max="500000"
              step="1000"
            />
          </div>
          <p className="mt-1 text-xs">
            Current baseline: £85,000 (2025-26)
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
                className="mt-1 mr-3 w-4 h-4 accent-black"
              />
              <div>
                <div className="font-medium">No taper</div>
                <div className="text-xs">Full VAT liability above threshold</div>
              </div>
            </label>
            
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                value="moderate"
                checked={reform.taper_type === 'moderate'}
                onChange={() => handleTaperTypeChange('moderate')}
                className="mt-1 mr-3 w-4 h-4 accent-black"
              />
              <div>
                <div className="font-medium">Moderate taper</div>
                <div className="text-xs">
                  Gradual increase from <span className="font-mono">£{Math.max(65000, reform.registration_threshold - 25000).toLocaleString()}</span> 
                  to <span className="font-mono">£{(reform.registration_threshold + 20000).toLocaleString()}</span>
                </div>
              </div>
            </label>
            
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                value="aggressive"
                checked={reform.taper_type === 'aggressive'}
                onChange={() => handleTaperTypeChange('aggressive')}
                className="mt-1 mr-3 w-4 h-4 accent-black"
              />
              <div>
                <div className="font-medium">Aggressive taper</div>
                <div className="text-xs">
                  Steeper increase from <span className="font-mono">£{Math.max(50000, reform.registration_threshold - 35000).toLocaleString()}</span> 
                  to <span className="font-mono">£{(reform.registration_threshold + 10000).toLocaleString()}</span>
                </div>
              </div>
            </label>
            
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                value="custom"
                checked={reform.taper_type === 'custom'}
                onChange={() => handleTaperTypeChange('custom')}
                className="mt-1 mr-3 w-4 h-4 accent-black"
              />
              <div>
                <div className="font-medium">Custom taper</div>
                <div className="text-xs">Define your own taper range</div>
              </div>
            </label>
          </div>
        </div>

        {reform.taper_type === 'custom' && (
          <div className="space-y-4 p-4 border border-black">
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
                  className="flex-1 px-3 py-2 border border-black font-mono focus:outline-none focus:ring-0"
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
                  className="flex-1 px-3 py-2 border border-black font-mono focus:outline-none focus:ring-0"
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
          className="w-full py-3 px-4 bg-black text-white font-medium hover:bg-white hover:text-black hover:border hover:border-black focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? 'Analysing...' : 'Analyse reform'}
        </button>
      </div>
    </form>
  );
}