import type { Metrics } from '@/lib/validation';
import { listWorkflows } from './workflow-service';
import { listExecutions } from './execution-service';
import { listUpcomingEvents } from './calendar-service';

/**
 * Aggregate overview metrics. Computes from the in-memory seeds so numbers
 * stay internally consistent with what the list pages show.
 */
export async function getMetrics(): Promise<Metrics> {
  const [workflows, executions, events] = await Promise.all([
    listWorkflows(),
    listExecutions(1000),
    listUpcomingEvents(14),
  ]);

  const activeCount = workflows.filter((w) => w.active).length;
  const oneDay = 24 * 3600_000;
  const now = Date.now();

  const last24h = executions.filter((e) => now - new Date(e.startedAt).getTime() <= oneDay);
  const completedLast24h = last24h.filter((e) => e.status === 'success' || e.status === 'error');
  const successLast24h = completedLast24h.filter((e) => e.status === 'success').length;

  const upcomingDeadlines = events.filter(
    (e) => e.kind === 'deadline' && new Date(e.start).getTime() - now <= 7 * oneDay,
  ).length;

  // 30-day time series — deterministic demo data
  const timeseries = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(now - (29 - i) * oneDay);
    const base = 38 + Math.sin(i / 3.4) * 12 + i * 0.4;
    const successes = Math.max(0, Math.round(base * (0.92 + Math.cos(i / 5) * 0.04)));
    return {
      date: d.toISOString().slice(0, 10),
      executions: Math.round(base),
      successes,
    };
  });

  return {
    activeWorkflows:   { value: activeCount,                                changePercent: 2.4 },
    executions24h:     { value: last24h.length,                             changePercent: 14.3 },
    successRate:       { value: completedLast24h.length === 0 ? 1 : successLast24h / completedLast24h.length, changePercent: 1.8 },
    upcomingDeadlines: { value: upcomingDeadlines,                          changePercent: -3.2 },
    timeseries,
  };
}
