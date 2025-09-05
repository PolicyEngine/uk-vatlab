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
  const previousValue = useRef(value);

  useEffect(() => {
    if (!ref.current) return;

    const interpolate = d3.interpolateNumber(previousValue.current, value);
    const timer = d3.timer((elapsed) => {
      const t = Math.min(1, elapsed / duration);
      const currentValue = interpolate(t);
      
      if (ref.current) {
        ref.current.textContent = format(currentValue);
      }
      
      if (t === 1) {
        timer.stop();
        previousValue.current = value;
      }
    });

    return () => timer.stop();
  }, [value, format, duration]);

  return <span ref={ref} className={`font-mono ${className}`}>{format(value)}</span>;
}