'use client';

export default function ReferenceLine() {
  return (
    <line 
      x1={0} 
      x2="100%" 
      y1={0} 
      y2={0} 
      stroke="#000" 
      strokeWidth={1}
      strokeDasharray="3 3"
    />
  );
}