'use client';

import { Bell, Plus, Search } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './theme-toggle';

export function Topbar() {
  const t = useTranslations('nav');
  return (
    <header
      role="banner"
      className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-surface px-8"
    >
      <div className="relative max-w-md flex-1">
        <label htmlFor="global-search" className="sr-only">
          {t('search')}
        </label>
        <Search
          aria-hidden="true"
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle"
        />
        <input
          id="global-search"
          type="search"
          placeholder={t('search')}
          className="h-9 w-full rounded-lg border border-border bg-surface-muted pl-9 pr-3 text-sm text-ink placeholder:text-ink-subtle transition-colors focus:border-primary focus:bg-surface focus:outline-none"
        />
      </div>
      <div className="flex items-center gap-2">
        <button
          aria-label="Benachrichtigungen"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
        >
          <Bell size={16} aria-hidden="true" />
        </button>
        <ThemeToggle />
        <div aria-hidden="true" className="mx-2 h-5 w-px bg-border" />
        <Button size="md" className="gap-2">
          <Plus size={14} strokeWidth={2.5} aria-hidden="true" />
          Neuer Workflow
        </Button>
      </div>
    </header>
  );
}
