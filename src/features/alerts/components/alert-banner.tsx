'use client';

import { useState } from 'react';
import { AlertTriangle, ChevronDown, Info, RotateCw } from 'lucide-react';
import type { Execution } from '@/lib/validation';
import { cn } from '@/lib/cn';

/**
 * Maps a workflow slug + error string to a human, actionable recommendation.
 * Keep this table here so adding new known-error playbooks is trivial.
 */
function recommendationFor(exec: Execution): string {
  const msg = (exec.errorMessage ?? '').toLowerCase();
  if (msg.includes('rate_limit')) {
    return 'Rate-Limit-Guard aktivieren oder API-Kontingent erhöhen. Automatischer Retry läuft in Kürze.';
  }
  if (msg.includes('approval timeout')) {
    return 'Manuell an Vertretung eskalieren oder Timeout-Schwellwert anpassen.';
  }
  if (msg.includes('low confidence')) {
    return 'Klassifizierer-Training prüfen oder Schwellwert senken. Manuell zuweisen bis zur Behebung.';
  }
  return 'Logs prüfen, Workflow neu starten oder an Support eskalieren.';
}

function primaryActionLabel(exec: Execution): string {
  const msg = (exec.errorMessage ?? '').toLowerCase();
  if (msg.includes('approval timeout')) return 'An Vertretung senden';
  return 'Jetzt neu starten';
}

export interface AlertBannerProps {
  failedExecutions: readonly Execution[];
}

export function AlertBanner({ failedExecutions }: AlertBannerProps) {
  const [open, setOpen] = useState(false);
  if (failedExecutions.length === 0) return null;

  const summary = failedExecutions
    .slice(0, 3)
    .map((e) => e.workflowName)
    .join(' · ');

  return (
    <section aria-label="Aktive Fehler" className="border-b border-border bg-warning-soft/60">
      <div className="mx-auto max-w-[1400px] px-8">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full items-center gap-4 py-3.5 text-left"
          aria-expanded={open}
        >
          <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-warning-soft text-warning">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-lg bg-warning/20" />
            <AlertTriangle className="relative" size={18} aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-ink">
                {failedExecutions.length} {failedExecutions.length === 1 ? 'Workflow' : 'Workflows'} mit Fehlern
              </span>
              <span className="label-xs text-warning">Aktion erforderlich</span>
            </div>
            <p className="mt-0.5 truncate text-xs text-ink-muted">{summary}</p>
          </div>
          <span className="hidden text-xs font-semibold text-warning sm:block">
            {open ? 'Schließen' : 'Details ansehen'}
          </span>
          <ChevronDown
            size={18}
            className={cn('text-ink-muted transition-transform duration-200', open && 'rotate-180')}
            aria-hidden="true"
          />
        </button>

        <div
          className={cn(
            'overflow-hidden transition-[max-height] duration-300 ease-out',
            open ? 'max-h-[800px]' : 'max-h-0',
          )}
        >
          <div className="space-y-3 pb-5">
            {failedExecutions.map((exec) => (
              <ErrorCard key={exec.id} exec={exec} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ErrorCard({ exec }: { exec: Execution }) {
  const recommendation = recommendationFor(exec);
  return (
    <article className="rounded-lg border border-warning/30 bg-surface">
      <div className="flex items-start gap-4 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-warning-soft text-warning">
          <AlertTriangle size={18} aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-ink">{exec.workflowName}</h3>
              <p className="mt-0.5 font-mono text-[11px] text-ink-subtle">
                {exec.id} · {relativeTime(exec.startedAt)}
              </p>
            </div>
            <span className="inline-flex shrink-0 items-center gap-1 rounded-md bg-warning-soft px-2 py-0.5 text-[11px] font-semibold text-warning">
              <span className="h-1.5 w-1.5 rounded-full bg-warning" />
              Fehler
            </span>
          </div>

          {exec.errorMessage && (
            <div className="mt-3 rounded-md bg-surface-muted px-3 py-2.5">
              <p className="label-xs mb-1">Fehlermeldung</p>
              <p className="break-words font-mono text-[12px] text-ink">{exec.errorMessage}</p>
            </div>
          )}

          <div className="mt-3 flex items-start gap-2.5 rounded-md bg-primary-soft/60 px-3 py-2.5">
            <Info className="mt-0.5 shrink-0 text-primary" size={14} aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-primary">Empfohlene Aktion</p>
              <p className="mt-0.5 text-xs text-ink">{recommendation}</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <button className="btn-hover inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-xs font-semibold text-primary-fg">
              <RotateCw size={12} strokeWidth={2.5} aria-hidden="true" />
              {primaryActionLabel(exec)}
            </button>
            <a
              href={`/workflows/${exec.workflowSlug}`}
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-xs font-medium text-ink transition-colors hover:bg-surface-muted"
            >
              Workflow öffnen
            </a>
            <button className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-3 text-xs font-medium text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink">
              Stummschalten
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function relativeTime(iso: string): string {
  const diffMin = Math.round((Date.now() - new Date(iso).getTime()) / 60_000);
  if (diffMin < 1) return 'jetzt';
  if (diffMin < 60) return `vor ${diffMin} Min.`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `vor ${diffH} Std.`;
  return `vor ${Math.round(diffH / 24)} T`;
}
