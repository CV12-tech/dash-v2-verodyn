'use client';

import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { Metrics } from '@/lib/validation';

export function ExecutionsChart({ data }: { data: Metrics['timeseries'] }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={[...data]} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradExec" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.12} />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="transparent" />
          <XAxis
            dataKey="date"
            tick={{ fill: 'hsl(var(--ink-subtle))', fontSize: 10, fontFamily: 'var(--font-sans)', fontWeight: 500 }}
            tickLine={false}
            axisLine={false}
            minTickGap={32}
          />
          <YAxis
            tick={{ fill: 'hsl(var(--ink-subtle))', fontSize: 10, fontFamily: 'var(--font-sans)', fontWeight: 500 }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              background: 'hsl(var(--surface))',
              border: '1px solid hsl(var(--border))',
              borderRadius: 8,
              fontSize: 12,
              fontFamily: 'var(--font-sans)',
              color: 'hsl(var(--ink))',
            }}
          />
          <Area
            type="monotone"
            dataKey="executions"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            fill="url(#gradExec)"
          />
          <Line
            type="monotone"
            dataKey="successes"
            stroke="hsl(var(--success))"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
