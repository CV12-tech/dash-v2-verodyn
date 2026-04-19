'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import {
  ChevronDown,
  MoreHorizontal,
  Play,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import type { Workflow, WorkflowCategory } from '@/lib/validation';
import { CATEGORY_BY_SLUG } from '@/lib/workflow-categories';
import { Sparkline } from '@/components/charts/sparkline';
import { cn } from '@/lib/cn';

type Token = 'primary' | 'success' | 'warning' | 'info';

function tokenClasses(token: Token) {
  return {
    primary: { fill: 'bg-primary-soft', text: 'text-primary', dot: 'bg-primary' },
    success: { fill: 'bg-success-soft', text: 'text-success', dot: 'bg-success' },
    warning: { fill: 'bg-warning-soft', text: 'text-warning', dot: 'bg-warning' },
    info: { fill: 'bg-info-soft', text: 'text-info', dot: 'bg-info' },
  }[token];
}

function fmtDuration(ms: number): string {
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)} s`;
  return `${(ms / 60_000).toFixed(1)} min`;
}

function relTimeHours(h: number | null): string {
  if (h === null) return '—';
  if (h < 1) return 'jetzt';
  if (h < 24) return `vor ${Math.round(h)} Std`;
  return `vor ${Math.round(h / 24)} T`;
}

/**
 * Derives the last-10-day success trend and last-7-runs pips from a workflow.
 * In production these would come from aggregate queries; here we synthesize
 * deterministic values from the workflow's success rate so the UI is stable.
 */
function derivePerformance(w: Workflow) {
  const seed = (w.slug.charCodeAt(0) * 31 + w.slug.length * 7) % 100;
  const spark = Array.from({ length: 10 }, (_, i) => {
    const jitter = (Math.sin(seed + i * 1.3) + Math.cos(seed * 0.7 + i)) * 0.015;
    return Math.max(0.8, Math.min(1.0, w.successRate + jitter));
  });
  const runs7: Array<'s' | 'e'> = Array.from({ length: 7 }, (_, i) => {
    const chance = (Math.sin(seed * 0.3 + i * 2.1) + 1) / 2; // 0..1
    return chance > (1 - w.successRate) ? 's' : 'e';
  });
  const execs7d = Math.round(24 * 7 * (w.triggerType === 'schedule' ? 0.5 : 0.3) * (0.5 + Math.sin(seed) * 0.5 + 0.5));
  return { spark, runs7, execs7d: Math.max(3, execs7d) };
}

export interface WorkflowTableProps {
  workflows: readonly Workflow[];
  activeCategory: WorkflowCategory | 'all';
}

export function WorkflowTable({ workflows, activeCategory }: WorkflowTableProps) {
  const t = useTranslations('workflows');
  const tTrigger = useTranslations('workflows.trigger');
  const [openSlugs, setOpenSlugs] = useState<Set<string>>(new Set());

  const filtered = useMemo(
    () => (activeCategory === 'all' ? workflows : workflows.filter((w) => w.category === activeCategory)),
    [workflows, activeCategory],
  );

  function toggle(slug: string) {
    setOpenSlugs((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-muted">
            <th scope="col" className="w-10 px-3 py-3" />
            <th scope="col" className="label-xs px-4 py-3 text-left">{t('columns.name')}</th>
            <th scope="col" className="label-xs px-4 py-3 text-left">Kategorie</th>
            <th scope="col" className="label-xs px-4 py-3 text-left">{t('columns.trigger')}</th>
            <th scope="col" className="label-xs px-4 py-3 text-left">{t('columns.lastRun')}</th>
            <th scope="col" className="label-xs px-4 py-3 text-left">{t('columns.successRate')}</th>
            <th scope="col" className="label-xs px-4 py-3 text-left">{t('columns.active')}</th>
            <th scope="col" className="px-6 py-3" />
          </tr>
        </thead>
        <tbody>
          {filtered.map((w) => {
            const cat = CATEGORY_BY_SLUG[w.category];
            const catClasses = tokenClasses(cat.token);
            const isOpen = openSlugs.has(w.slug);
            const successPct = Math.round(w.successRate * 100);
            const successClass =
              successPct >= 95 ? 'text-success' : successPct >= 90 ? 'text-ink' : 'text-warning';
            const perf = derivePerformance(w);
            const recentFailures = perf.runs7.filter((r) => r === 'e').length;
            const trendStart = perf.spark[0]!;
            const trendEnd = perf.spark[perf.spark.length - 1]!;
            const trendDelta = (trendEnd - trendStart) * 100;
            const TrendIcon = trendDelta >= 0 ? ArrowUpRight : ArrowDownRight;
            const trendColor = trendDelta >= 0 ? 'text-success' : 'text-warning';
            const sparkColor =
              successPct >= 95 ? 'hsl(var(--success))' : successPct >= 90 ? 'hsl(var(--primary))' : 'hsl(var(--warning))';

            return (
              <ExpandableWorkflowRow
                key={w.slug}
                workflow={w}
                isOpen={isOpen}
                onToggle={() => toggle(w.slug)}
                catLabel={t(`categories.${w.category}` as 'categories.client-lifecycle')}
                catClasses={catClasses}
                triggerLabel={tTrigger(w.triggerType)}
                successPct={successPct}
                successClass={successClass}
                perf={perf}
                recentFailures={recentFailures}
                trendDelta={trendDelta}
                TrendIcon={TrendIcon}
                trendColor={trendColor}
                sparkColor={sparkColor}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

interface RowProps {
  workflow: Workflow;
  isOpen: boolean;
  onToggle: () => void;
  catLabel: string;
  catClasses: { fill: string; text: string; dot: string };
  triggerLabel: string;
  successPct: number;
  successClass: string;
  perf: { spark: number[]; runs7: Array<'s' | 'e'>; execs7d: number };
  recentFailures: number;
  trendDelta: number;
  TrendIcon: typeof ArrowUpRight;
  trendColor: string;
  sparkColor: string;
}

function ExpandableWorkflowRow({
  workflow: w,
  isOpen,
  onToggle,
  catLabel,
  catClasses,
  triggerLabel,
  successPct,
  successClass,
  perf,
  recentFailures,
  trendDelta,
  TrendIcon,
  trendColor,
  sparkColor,
}: RowProps) {
  const lastRunHours = w.lastRunAt ? (Date.now() - new Date(w.lastRunAt).getTime()) / 3_600_000 : null;
  return (
    <>
      <tr
        onClick={onToggle}
        className={cn(
          'cursor-pointer border-b border-border transition-colors last:border-0 hover:bg-surface-muted/40',
          isOpen && 'bg-surface-muted/30',
        )}
        aria-expanded={isOpen}
      >
        <td className="px-3 py-4 text-center">
          <ChevronDown
            size={14}
            className={cn('inline-block text-ink-subtle transition-transform', isOpen && 'rotate-180')}
            aria-hidden="true"
          />
        </td>
        <td className="px-4 py-4">
          <div className="font-medium text-ink">{w.name}</div>
          <div className="font-mono text-[11px] text-ink-subtle">{w.slug}</div>
        </td>
        <td className="px-4 py-4">
          <span className={cn('inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-semibold', catClasses.fill, catClasses.text)}>
            <span className={cn('h-1.5 w-1.5 rounded-full', catClasses.dot)} />
            {catLabel}
          </span>
        </td>
        <td className="px-4 py-4 text-xs text-ink-muted">{triggerLabel}</td>
        <td className="px-4 py-4 text-xs text-ink-muted">{relTimeHours(lastRunHours)}</td>
        <td className="px-4 py-4">
          <span className={cn('nums text-sm font-semibold', successClass)}>{successPct} %</span>
        </td>
        <td className="px-4 py-4">
          {w.active ? (
            <span className="inline-flex items-center gap-1.5 rounded-md bg-success-soft px-2 py-1 text-[11px] font-semibold text-success">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Aktiv
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-md bg-surface-muted px-2 py-1 text-[11px] font-semibold text-ink-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-ink-subtle" />
              Inaktiv
            </span>
          )}
        </td>
        <td className="px-6 py-4 text-right">
          <button
            onClick={(e) => e.stopPropagation()}
            aria-label="Aktionen"
            className="inline-flex h-7 w-7 items-center justify-center rounded-md text-ink-subtle transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <MoreHorizontal size={14} aria-hidden="true" />
          </button>
        </td>
      </tr>

      {isOpen && (
        <tr>
          <td colSpan={8} className="border-b border-border bg-surface-muted/40 p-0">
            <div className="px-8 py-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <PanelRuns runs={perf.runs7} />
                <PanelTrend
                  trendEndPct={Math.round(perf.spark[perf.spark.length - 1]! * 100)}
                  trendDelta={trendDelta}
                  TrendIcon={TrendIcon}
                  trendColor={trendColor}
                  spark={perf.spark}
                  sparkColor={sparkColor}
                />
                <PanelDuration avgMs={w.avgDurationMs} nodes={w.nodeCount} connections={w.connectionCount} />
                <PanelThroughput execs7d={perf.execs7d} />
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-2">
                <button className="btn-hover inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-xs font-semibold text-primary-fg">
                  <Play size={12} strokeWidth={2.5} aria-hidden="true" />
                  Jetzt ausführen
                </button>
                <Link
                  href={`/workflows/${w.slug}`}
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-xs font-medium text-ink transition-colors hover:bg-surface-muted"
                >
                  Verlauf öffnen
                </Link>
                <button className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-xs font-medium text-ink transition-colors hover:bg-surface-muted">
                  In n8n bearbeiten
                </button>
                {recentFailures > 0 && (
                  <span className="ml-auto inline-flex items-center gap-1.5 text-[11px] text-warning">
                    <AlertTriangle size={12} aria-hidden="true" />
                    {recentFailures} Fehler in den letzten 7 Läufen
                  </span>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function PanelRuns({ runs }: { runs: Array<'s' | 'e'> }) {
  const ok = runs.filter((r) => r === 's').length;
  const err = runs.length - ok;
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="label-xs">Letzte 7 Läufe</p>
      <div className="mt-3 flex items-center gap-1">
        {runs.map((r, i) => (
          <span
            key={i}
            className={cn('h-5 w-1.5 rounded-sm', r === 's' ? 'bg-success' : 'bg-warning')}
          />
        ))}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[11px]">
        <span className="inline-flex items-center gap-1 text-success">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          {ok} ok
        </span>
        <span className="inline-flex items-center gap-1 text-warning">
          <span className="h-1.5 w-1.5 rounded-full bg-warning" />
          {err} Fehler
        </span>
      </div>
    </div>
  );
}

function PanelTrend({
  trendEndPct,
  trendDelta,
  TrendIcon,
  trendColor,
  spark,
  sparkColor,
}: {
  trendEndPct: number;
  trendDelta: number;
  TrendIcon: typeof ArrowUpRight;
  trendColor: string;
  spark: number[];
  sparkColor: string;
}) {
  const sign = trendDelta > 0 ? '+' : '';
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="label-xs">Erfolgstrend · 10 T</p>
          <p className="nums mt-1 text-lg font-bold text-ink">{trendEndPct} %</p>
        </div>
        <span className={cn('inline-flex items-center gap-0.5 text-[11px] font-semibold', trendColor)}>
          <TrendIcon size={10} strokeWidth={3} aria-hidden="true" />
          {sign}
          {trendDelta.toFixed(1)} pp
        </span>
      </div>
      <div className="-mx-1 -mb-1 mt-2">
        <Sparkline values={spark} color={sparkColor} />
      </div>
    </div>
  );
}

function PanelDuration({ avgMs, nodes, connections }: { avgMs: number; nodes: number; connections: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="label-xs">Ø Dauer</p>
      <p className="nums mt-3 text-lg font-bold text-ink">{fmtDuration(avgMs)}</p>
      <p className="mt-1 text-[11px] text-ink-muted">
        {nodes} Knoten · {connections} Kanten
      </p>
    </div>
  );
}

function PanelThroughput({ execs7d }: { execs7d: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="label-xs">Durchsatz · 7 T</p>
      <p className="nums mt-3 text-lg font-bold text-ink">{execs7d}</p>
      <p className="mt-1 text-[11px] text-ink-muted">Ø {(execs7d / 7).toFixed(1)} pro Tag</p>
    </div>
  );
}
