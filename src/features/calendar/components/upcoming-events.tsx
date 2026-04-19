'use client';

import { useTranslations } from 'next-intl';
import { Calendar as CalendarIcon } from 'lucide-react';
import type { CalendarEvent } from '@/lib/validation';
import { cn } from '@/lib/cn';

const KIND_CLASSES: Record<CalendarEvent['kind'], { fill: string; text: string }> = {
  meeting: { fill: 'bg-primary-soft', text: 'text-primary' },
  deadline: { fill: 'bg-warning-soft', text: 'text-warning' },
  review: { fill: 'bg-info-soft', text: 'text-info' },
  protocol: { fill: 'bg-success-soft', text: 'text-success' },
};

export function UpcomingEvents({ events, limit = 5 }: { events: readonly CalendarEvent[]; limit?: number }) {
  const tKind = useTranslations('calendar.kind');
  const upcoming = [...events]
    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    .slice(0, limit);

  return (
    <ul className="divide-y divide-border">
      {upcoming.map((e) => {
        const cls = KIND_CLASSES[e.kind];
        const at = new Date(e.start);
        const date = at.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: 'short' });
        const time = at.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        const hasTime = new Date(e.end).getTime() > new Date(e.start).getTime();
        return (
          <li key={e.id} className="flex gap-3 px-5 py-3.5 transition-colors hover:bg-surface-muted/40">
            <div
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                cls.fill,
                cls.text,
              )}
            >
              <CalendarIcon size={14} aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="line-clamp-2 text-sm font-medium text-ink">{e.subject}</div>
              <div className="mt-0.5 flex items-center gap-2 text-[11px] text-ink-muted">
                <span className={cn('font-semibold', cls.text)}>{tKind(e.kind)}</span>
                <span aria-hidden="true">·</span>
                <span>{date}{hasTime ? `, ${time}` : ''}</span>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
