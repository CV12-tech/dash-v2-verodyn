'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import type { CalendarEvent } from '@/lib/validation';
import { cn } from '@/lib/cn';

type Token = 'primary' | 'warning' | 'info' | 'success';

const KIND_TOKEN: Record<CalendarEvent['kind'], Token> = {
  meeting: 'primary',
  deadline: 'warning',
  review: 'info',
  protocol: 'success',
};

function tokenClasses(token: Token) {
  return {
    primary: { text: 'text-primary', dot: 'bg-primary' },
    warning: { text: 'text-warning', dot: 'bg-warning' },
    info:    { text: 'text-info',    dot: 'bg-info' },
    success: { text: 'text-success', dot: 'bg-success' },
  }[token];
}

function startOfWeek(d: Date): Date {
  const copy = new Date(d);
  const day = (copy.getDay() + 6) % 7; // Monday = 0
  copy.setHours(0, 0, 0, 0);
  copy.setDate(copy.getDate() - day);
  return copy;
}

export interface CalendarWeekProps {
  events: readonly CalendarEvent[];
  compact?: boolean;
}

export function CalendarWeek({ events, compact = false }: CalendarWeekProps) {
  const t = useTranslations('calendar');
  const tKind = useTranslations('calendar.kind');
  const dayLabels = useMemo(() => {
    try {
      return (t.raw('days') as string[]) ?? ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
    } catch {
      return ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
    }
  }, [t]);

  const today = new Date();
  const weekStart = startOfWeek(today);
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  return (
    <div className="rounded-lg border border-border bg-surface">
      {/* Day headers */}
      <div className="grid grid-cols-7 border-b border-border">
        {days.map((d) => {
          const isToday = d.toDateString() === today.toDateString();
          return (
            <div
              key={d.toISOString()}
              className={cn(
                'border-r border-border last:border-r-0',
                compact ? 'px-3 py-2.5' : 'px-4 py-3',
              )}
            >
              <div className="label-xs">{dayLabels[(d.getDay() + 6) % 7]}</div>
              <div className="mt-0.5 flex items-center gap-2">
                <span
                  className={cn(
                    'nums font-bold',
                    compact ? 'text-sm' : 'text-lg',
                    isToday ? 'text-primary' : 'text-ink',
                  )}
                >
                  {d.getDate()}
                </span>
                {isToday && (
                  <span
                    className={cn(
                      'rounded-md bg-primary-soft font-semibold uppercase tracking-wide text-primary',
                      compact ? 'px-1 py-0.5 text-[9px]' : 'px-1.5 py-0.5 text-[10px]',
                    )}
                  >
                    {t('today')}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7">
        {days.map((d) => {
          const dayStart = new Date(d);
          dayStart.setHours(0, 0, 0, 0);
          const dayEnd = new Date(d);
          dayEnd.setHours(23, 59, 59, 999);
          const dayEvents = events
            .filter((e) => {
              const at = new Date(e.start);
              return at >= dayStart && at <= dayEnd;
            })
            .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

          return (
            <div
              key={d.toISOString()}
              className={cn(
                'space-y-1.5 border-b border-r border-border p-2 last:border-r-0',
                compact ? 'min-h-[130px]' : 'min-h-[200px]',
              )}
            >
              {dayEvents.length === 0 ? (
                <div className="text-[11px] text-ink-subtle">—</div>
              ) : (
                dayEvents.map((e) => {
                  const tok = tokenClasses(KIND_TOKEN[e.kind]);
                  const time = new Date(e.start).toLocaleTimeString('de-DE', {
                    hour: '2-digit',
                    minute: '2-digit',
                  });
                  return (
                    <button
                      key={e.id}
                      type="button"
                      className={cn(
                        'w-full rounded-md border border-border bg-surface text-left transition-colors hover:bg-surface-muted',
                        compact ? 'px-2 py-1.5' : 'px-2.5 py-2',
                      )}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className={cn('h-1.5 w-1.5 shrink-0 rounded-full', tok.dot)} />
                        <span className="nums text-[11px] font-semibold text-ink">{time}</span>
                        <span className={cn('ml-auto text-[9px] font-medium', tok.text)}>
                          {tKind(e.kind)}
                        </span>
                      </div>
                      <div
                        className={cn(
                          'font-medium text-ink',
                          compact ? 'mt-0.5 line-clamp-1 text-[11px]' : 'mt-1 line-clamp-2 text-[11px]',
                        )}
                      >
                        {e.subject}
                      </div>
                      {e.location && !compact && (
                        <div className="mt-0.5 truncate text-[10px] text-ink-muted">{e.location}</div>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
