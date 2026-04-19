'use client';

import { useTranslations } from 'next-intl';
import { ChevronRight } from 'lucide-react';
import type { Execution, ExecutionStatus } from '@/lib/validation';
import { cn } from '@/lib/cn';

const STATUS_CLASSES: Record<ExecutionStatus, string> = {
  success: 'bg-success-soft text-success',
  error: 'bg-warning-soft text-warning',
  running: 'bg-info-soft text-info',
  pending: 'bg-surface-muted text-ink-muted',
  cancelled: 'bg-surface-muted text-ink-muted',
};

function relTime(iso: string): string {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60_000);
  if (min < 1) return 'jetzt';
  if (min < 60) return `vor ${min} Min`;
  if (min < 1440) return `vor ${Math.round(min / 60)} Std`;
  return `vor ${Math.round(min / 1440)} T`;
}

export function RecentExecutions({ executions, limit = 6 }: { executions: readonly Execution[]; limit?: number }) {
  const tStatus = useTranslations('executions.status');

  return (
    <ul className="divide-y divide-border">
      {executions.slice(0, limit).map((e) => (
        <li
          key={e.id}
          className="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-surface-muted/40"
        >
          <span className={cn('inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold', STATUS_CLASSES[e.status])}>
            {tStatus(e.status)}
          </span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-ink">{e.workflowName}</div>
            <div className="text-[11px] text-ink-muted">{relTime(e.startedAt)}</div>
          </div>
          <ChevronRight size={14} className="shrink-0 text-ink-subtle" aria-hidden="true" />
        </li>
      ))}
    </ul>
  );
}
