'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';

import { WorkflowTable } from '@/features/workflows/components/workflow-table';
import { Skeleton } from '@/components/ui/skeleton';
import { useWorkflows } from '@/features/dashboard/hooks';
import { CATEGORIES } from '@/lib/workflow-categories';
import type { WorkflowCategory } from '@/lib/validation';
import { cn } from '@/lib/cn';

type Filter = WorkflowCategory | 'all';

export default function WorkflowsPage() {
  const t = useTranslations('workflows');
  const { data: workflows, isLoading } = useWorkflows();
  const searchParams = useSearchParams();
  const urlCategory = searchParams.get('category') as WorkflowCategory | null;
  const [active, setActive] = useState<Filter>(urlCategory ?? 'all');

  const chips = useMemo(() => {
    const all = { slug: 'all' as const, label: 'Alle', count: workflows?.length ?? 0 };
    const byCat = CATEGORIES.map((c) => ({
      slug: c.slug,
      label: c.labelDe,
      count: (workflows ?? []).filter((w) => w.category === c.slug).length,
    }));
    return [all, ...byCat];
  }, [workflows]);

  return (
    <div className="mx-auto max-w-[1400px] px-8 py-10 space-y-8">
      <header>
        <p className="label-xs mb-1">Modul</p>
        <h1 className="text-3xl font-bold tracking-tight text-ink">{t('title')}</h1>
        <p className="mt-1.5 text-sm text-ink-muted">{t('subtitle')} · Zeile klicken für Performance-Details</p>
      </header>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Kategorie-Filter">
        {chips.map((chip) => {
          const isActive = chip.slug === active;
          return (
            <button
              key={chip.slug}
              onClick={() => setActive(chip.slug as Filter)}
              role="tab"
              aria-selected={isActive}
              className={cn(
                'inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors',
                isActive
                  ? 'border-primary bg-primary-soft text-primary'
                  : 'border-border bg-surface text-ink-muted hover:bg-surface-muted hover:text-ink',
              )}
            >
              {chip.label}
              <span
                className={cn(
                  'nums rounded-full px-1.5 py-0.5 text-[10px] font-bold',
                  isActive ? 'bg-primary/10 text-primary' : 'bg-surface-muted text-ink-subtle',
                )}
              >
                {chip.count}
              </span>
            </button>
          );
        })}
      </div>

      {isLoading || !workflows ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <WorkflowTable workflows={workflows} activeCategory={active} />
      )}
    </div>
  );
}
