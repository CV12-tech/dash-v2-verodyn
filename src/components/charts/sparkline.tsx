interface SparklineProps {
  values: readonly number[];
  min?: number;
  max?: number;
  color: string; // CSS color
  width?: number;
  height?: number;
  className?: string;
}

/**
 * Accessible mini-chart. Uses CSS color vars from the design system so it
 * picks up theme changes automatically. Fully SSR-safe (no refs or effects).
 */
export function Sparkline({
  values,
  min = 0.8,
  max = 1.0,
  color,
  width = 120,
  height = 32,
  className,
}: SparklineProps) {
  if (values.length === 0) return null;
  const pad = 2;
  const x = (i: number) => pad + (i / (values.length - 1)) * (width - 2 * pad);
  const y = (v: number) => pad + (1 - (v - min) / (max - min)) * (height - 2 * pad);
  const path = values.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(v)}`).join(' ');
  const area = `${path} L${x(values.length - 1)},${height - pad} L${x(0)},${height - pad} Z`;
  const gradId = `spark-grad-${Math.random().toString(36).slice(2, 10)}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={className}
      role="img"
      aria-label="Trend"
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.18} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradId})`} />
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
