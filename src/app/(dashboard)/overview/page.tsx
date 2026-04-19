'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { Workflow, Activity, CheckCircle2, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

import { AlertBanner } from '@/features/alerts/components/alert-banner';
import { StatCard } from '@/features/dashboard/components/stat-card';
import { CalendarWeek } from '@/features/calendar/components/calendar-week';
import { RecentExecutions } from '@/features/executions/components/recent-executions';
import { ExecutionsChart } from '@/features/metrics/components/executions-chart';
import { Skeleton } from '@/components/ui/skeleton';
import { CATEGORIES } from '@/lib/workflow-categories';
import {
  useMetrics,
  useExecutions,
  useCalendarEvents,
  useWorkflows,
} from '@/features/dashboard/hooks';

function formatCount(n: number): string {
  return new Intl.NumberFormat('de-DE').format(n);
}

function formatPercent(v: number): string {
  return `${(v * 100).toFixed(1).replace('.', ',')} %`;
}

const CATEGORY_TONE = {
  primary: 'bg-primary-soft text-primary',
  success: 'bg-success-soft text-success',
  warning: 'bg-warning-soft text-warning',
  info: 'bg-info-soft text-info',
} as const;

export default function OverviewPage() {
  const t = useTranslations('overview');
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: executions, isLoading: execsLoading } = useExecutions(50);
  const { data: events, isLoading: eventsLoading } = useCalendarEvents(7);
  const { data: workflows } = useWorkflows();

  const failedExecutions = useMemo(
    () => (executions ?? []).filter((e) => e.status === 'error').slice(0, 5),
    [executions],
  );

  return (
    <>
      <AlertBanner failedExecutions={failedExecutions} />

      <div className="mx-auto max-w-[1400px] px-8 py-10">
        <div className="space-y-10">
          {/* Header */}
          <header className="flex items-end justify-between gap-4">
            <div>
              <p className="label-xs mb-1">Workspace · Kanzlei Demo</p>
              <h1 className="text-3xl font-bold tracking-tight text-ink">{t('title')}</h1>
              <p className="mt-1.5 text-sm text-ink-muted">{t('subtitle')}</p>
            </div>
            <div className="hidden items-center gap-1 rounded-lg border border-border bg-surface p-1 md:flex">
              <button className="rounded-md bg-surface-muted px-3 py-1.5 text-xs font-semibold text-ink">24 h</button>
              <button className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:text-ink">7 T</button>
              <button className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:text-ink">30 T</button>
              <button className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:text-ink">90 T</button>
            </div>
          </header>

          {/* Stat cards */}
          <section
            aria-labelledby="stats-heading"
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
          >
            <h2 id="stats-heading" className="sr-only">Kennzahlen</h2>
            {metricsLoading || !metrics ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[132px]" />)
            ) : (
              <>
                <StatCard
                  label={t('stats.activeWorkflows')}
                  value={formatCount(metrics.activeWorkflows.value)}
                  subValue={workflows ? `/${workflows.length}` : undefined}
                  changePercent={metrics.activeWorkflows.changePercent}
                  changeSuffix="vs. Vorwoche"
                  icon={Workflow}
                  tone="primary"
                />
                <StatCard
                  label={t('stats.executions24h')}
                  value={formatCount(metrics.executions24h.value)}
                  changePercent={metrics.executions24h.changePercent}
                  changeSuffix="vs. Vortag"
                  icon={Activity}
                  tone="success"
                />
                <StatCard
                  label={t('stats.successRate')}
                  value={formatPercent(metrics.successRate.value)}
                  changePercent={metrics.successRate.changePercent}
                  changeSuffix="vs. Vorwoche"
                  icon={CheckCircle2}
                  tone="info"
                />
                <StatCard
                  label={t('stats.upcomingDeadlines')}
                  value={formatCount(metrics.upcomingDeadlines.value)}
                  changePercent={metrics.upcomingDeadlines.changePercent}
                  changeSuffix="in nächsten 7 T"
                  icon={Clock}
                  tone="warning"
                  invertTrend
                />
              </>
            )}
          </section>

          {/* Calendar hero */}
          <section aria-labelledby="calendar-heading">
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <h2 id="calendar-heading" className="text-base font-semibold text-ink">Kalenderwoche</h2>
                <p className="mt-0.5 text-xs text-ink-muted">Termine, Fristen und Reviews</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  aria-label="Vorherige Woche"
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
                >
                  <ChevronLeft size={14} aria-hidden="true" />
                </button>
                <div className="min-w-[200px] rounded-lg border border-border bg-surface px-4 py-1.5 text-center text-xs font-semibold text-ink">
                  Diese Woche
                </div>
                <button
                  aria-label="Nächste Woche"
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
                >
                  <ChevronRight size={14} aria-hidden="true" />
                </button>
                <Link
                  href="/calendar"
                  className="ml-1 inline-flex h-8 items-center gap-1 rounded-lg border border-border bg-surface px-3 text-xs font-semibold text-ink transition-colors hover:bg-surface-muted"
                >
                  Volle Ansicht
                  <ChevronRight size={12} strokeWidth={2.5} aria-hidden="true" />
                </Link>
              </div>
            </div>
            {eventsLoading || !events ? (
              <Skeleton className="h-[280px]" />
            ) : (
              <CalendarWeek events={events} compact />
            )}
            <div className="mt-3 flex flex-wrap items-center gap-5 text-[11px] text-ink-muted">
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-sm bg-primary" />Termin</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-sm bg-warning" />Frist</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-sm bg-info" />Review</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-sm bg-success" />Protokoll</div>
            </div>
          </section>

          {/* Auswertung left + executions right */}
          <section className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-lg border border-border bg-surface p-6 lg:col-span-2">
              <div className="mb-6 flex items-end justify-between">
                <div>
                  <h2 className="text-base font-semibold text-ink">Auswertung · Ausführungen 30 Tage</h2>
                  <p className="mt-0.5 text-xs text-ink-muted">Tägliche Läufe und Erfolge</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-primary" />
                    <span className="text-xs text-ink-muted">{t('chart.executions')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-success" />
                    <span className="text-xs text-ink-muted">{t('chart.successes')}</span>
                  </div>
                </div>
              </div>
              {metricsLoading || !metrics ? <Skeleton className="h-72" /> : <ExecutionsChart data={metrics.timeseries} />}
            </div>

            <div className="rounded-lg border border-border bg-surface">
              <div className="flex items-center justify-between border-b border-border px-6 py-4">
                <h2 className="text-base font-semibold text-ink">{t('sections.recentExecutions')}</h2>
                <Link href="/executions" className="text-xs font-semibold text-primary hover:underline">
                  Alle ansehen
                </Link>
              </div>
              {execsLoading || !executions ? (
                <div className="space-y-2 p-5">
                  {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : (
                <RecentExecutions executions={executions} />
              )}
            </div>
          </section>

          {/* Categories */}
          <section aria-labelledby="categories-heading">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <h2 id="categories-heading" className="text-base font-semibold text-ink">Workflow-Kategorien</h2>
                <p className="mt-0.5 text-xs text-ink-muted">Ihre Automatisierungen über die fünf Domänen</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {CATEGORIES.map((c) => {
                const count = (workflows ?? []).filter((w) => w.category === c.slug).length;
                return (
                  <Link
                    key={c.slug}
                    href={`/workflows?category=${c.slug}`}
                    className="group rounded-lg border border-border bg-surface p-5 transition-colors hover:bg-surface-muted/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${CATEGORY_TONE[c.token]}`}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect width="7" height="7" x="3" y="3" rx="1" />
                          <rect width="7" height="7" x="14" y="3" rx="1" />
                          <rect width="7" height="7" x="14" y="14" rx="1" />
                          <rect width="7" height="7" x="3" y="14" rx="1" />
                        </svg>
                      </div>
                      <span className="nums text-xl font-bold text-ink">{count}</span>
                    </div>
                    <h3 className="mt-4 text-sm font-semibold text-ink">{c.labelDe}</h3>
                    <p className="mt-1 line-clamp-2 text-xs text-ink-muted">{c.description}</p>
                  </Link>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
