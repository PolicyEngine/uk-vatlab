import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // For now, return mock data - we'll implement the actual logic later
    const mockResponse = {
      registration_threshold: body.registration_threshold || 90000,
      taper_type: body.taper_type || 'none',
      revenue_impact: {
        '2025-26': Math.random() * 1000 - 500, // Random revenue impact
        '2026-27': Math.random() * 1000 - 500,
        '2027-28': Math.random() * 1000 - 500,
        '2028-29': Math.random() * 1000 - 500,
        '2029-30': Math.random() * 1000 - 500,
        '2030-31': Math.random() * 1000 - 500,
      },
      firms_impact: {
        newly_registered: Math.floor(Math.random() * 50000),
        newly_deregistered: Math.floor(Math.random() * 30000),
        net_change: Math.floor(Math.random() * 80000 - 40000),
      },
      summary: {
        total_revenue_impact: Math.random() * 2000 - 1000,
        average_annual_impact: Math.random() * 400 - 200,
      }
    };

    return NextResponse.json(mockResponse);
  } catch (error) {
    console.error('Analysis error:', error);
    return NextResponse.json(
      { detail: 'Failed to analyze reform' },
      { status: 500 }
    );
  }
}