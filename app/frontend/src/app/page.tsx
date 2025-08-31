'use client';

import { useState } from 'react';
import axios from 'axios';
import PolicyForm from '@/components/PolicyForm';
import ResultsDisplay from '@/components/ResultsDisplay';
import { PolicyReform, PolicyAnalysisResult } from '@/types';

export default function Home() {
  const [results, setResults] = useState<PolicyAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitReform = async (reform: PolicyReform) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post<PolicyAnalysisResult>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze`,
        reform
      );
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyse reform. Please try again.');
      console.error('Error analysing reform:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 border-b-2 border-black pb-4">
          <h1 className="text-4xl font-medium tracking-tight">
            VAT policy simulator
          </h1>
          <p className="text-sm mt-2">
            Analyse the fiscal impact of VAT registration threshold reforms over the budget window (2025-26 to 2030-31)
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <PolicyForm onSubmit={handleSubmitReform} isLoading={isLoading} />
            
            {error && (
              <div className="mt-4 p-4 border border-black">
                <p className="text-sm font-bold">{error}</p>
              </div>
            )}
            
            <div className="mt-6 border border-black p-4">
              <h3 className="font-medium mb-2">About</h3>
              <p className="text-xs">
                This tool uses synthetic firm data to estimate the revenue impact of changes to the VAT registration threshold. 
                The model accounts for firm growth, sectoral differences, and various tapering options to smooth the transition 
                for businesses near the threshold.
              </p>
            </div>
          </div>

          <div className="lg:col-span-2">
            {results ? (
              <ResultsDisplay results={results} />
            ) : (
              <div className="border-2 border-black p-12 text-center">
                <svg className="mx-auto h-24 w-24 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="text-xl font-medium mb-2">Design a reform to see results</h3>
                <p className="text-sm">
                  Configure the VAT registration threshold and tapering options to analyse their fiscal impact.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}