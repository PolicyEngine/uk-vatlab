'use client';

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface AnimatedNumberProps {
  value: number;
  format?: (value: number) => string;
  duration?: number;
  className?: string;
}

export default function AnimatedNumber({ 
  value, 
  format = (v) => v.toString(), 
  duration = 750,
  className = ''
}: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const sanitized = Number.isFinite(value) ? value : 0;
  const previousValue = useRef(sanitized);

  useEffect(() => {
    if (!ref.current) return;

    const next = Number.isFinite(value) ? value : 0;
    const interpolate = d3.interpolateNumber(previousValue.current, next);
    const timer = d3.timer((elapsed) => {
      const t = Math.min(1, elapsed / duration);
      const currentValue = interpolate(t);
      
      if (ref.current) {
        ref.current.textContent = format(currentValue);
      }
      
      if (t === 1) {
        timer.stop();
        previousValue.current = next;
      }
    });

    return () => timer.stop();
  }, [value, format, duration]);

  return <span ref={ref} className={`font-mono ${className}`}>{format(sanitized)}</span>;
}
