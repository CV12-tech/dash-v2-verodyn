'use client';

import { useTranslations } from 'next-intl';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { CalendarWeek } from '@/features/calendar/components/calendar-week';
import { UpcomingEvents } from '@/features/calendar/components/upcoming-events';
import { Skeleton } from '@/components/ui/skeleton';
import { useCalendarEvents } from '@/features/dashboard/hooks';

export default function CalendarPage() {
  const t = useTranslations('calendar');
  const { data: events, isLoading } = useCalendarEvents(14);

  return (
    <div className="mx-auto max-w-[1400px] px-8 py-10 space-y-8">
      <header className="flex items-end justify-between gap-4">
        <div>
          <p className="label-xs mb-1">Modul</p>
          <h1 className="text-3xl font-bold tracking-tight text-ink">{t('title')}</h1>
          <p className="mt-1.5 text-sm text-ink-muted">{t('subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            aria-label="Vorherige Woche"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <ChevronLeft size={16} aria-hidden="true" />
          </button>
          <div className="min-w-[220px] rounded-lg border border-border bg-surface px-4 py-2 text-center text-sm font-semibold text-ink">
            Diese Woche
          </div>
          <button
            aria-label="Nächste Woche"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {isLoading || !events ? (
          <>
            <Skeleton className="h-[500px]" />
            <Skeleton className="h-[500px]" />
          </>
        ) : (
          <>
            <CalendarWeek events={events} />
            <aside className="rounded-lg border border-border bg-surface">
              <div className="border-b border-border px-5 py-4">
                <h2 className="text-sm font-semibold text-ink">Anstehend</h2>
                <p className="mt-0.5 text-xs text-ink-muted">Nächste 5 Termine</p>
              </div>
              <UpcomingEvents events={events} />
            </aside>
          </>
        )}
      </div>
    </div>
  );
}
