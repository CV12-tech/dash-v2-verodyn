'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useTranslations } from 'next-intl';
import {
  LayoutGrid,
  Workflow as WorkflowIcon,
  Activity,
  Calendar as CalendarIcon,
  CheckSquare,
  Settings as SettingsIcon,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import { signOut } from 'next-auth/react';

import { cn } from '@/lib/cn';
import { can, type Permission } from '@/lib/rbac';

interface NavItem {
  href: string;
  labelKey: 'overview' | 'workflows' | 'executions' | 'calendar' | 'tasks' | 'settings';
  icon: LucideIcon;
  permission: Permission;
  group: 'workspace' | 'admin';
}

const NAV: readonly NavItem[] = [
  { href: '/overview',   labelKey: 'overview',   icon: LayoutGrid,    permission: 'workflows.read',  group: 'workspace' },
  { href: '/workflows',  labelKey: 'workflows',  icon: WorkflowIcon,  permission: 'workflows.read',  group: 'workspace' },
  { href: '/executions', labelKey: 'executions', icon: Activity,      permission: 'executions.read', group: 'workspace' },
  { href: '/calendar',   labelKey: 'calendar',   icon: CalendarIcon,  permission: 'calendar.read',   group: 'workspace' },
  { href: '/tasks',      labelKey: 'tasks',      icon: CheckSquare,   permission: 'tasks.close',     group: 'workspace' },
  { href: '/settings',   labelKey: 'settings',   icon: SettingsIcon,  permission: 'settings.read',   group: 'admin' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const t = useTranslations('nav');
  const tApp = useTranslations('app');
  const role = session?.user?.role;

  const workspace = NAV.filter((n) => n.group === 'workspace' && can(role, n.permission));
  const admin = NAV.filter((n) => n.group === 'admin' && can(role, n.permission));

  return (
    <aside
      aria-label="Primary"
      className="hidden w-64 shrink-0 border-r border-border bg-surface-muted md:flex md:flex-col"
    >
      <div className="flex h-16 items-center px-6">
        <Link href="/overview" className="flex items-center gap-2.5">
          <span className="relative flex h-8 w-8 items-center justify-center">
            <span className="absolute inset-0 rounded-lg bg-primary-soft" />
            <svg className="relative text-primary" width="18" height="18" viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 12 L16 6 L24 12 L24 20 L16 26 L8 20 Z" />
              <circle cx="16" cy="16" r="3" fill="currentColor" />
            </svg>
          </span>
          <span className="leading-tight">
            <span className="block text-[15px] font-bold tracking-tight text-ink">{tApp('name')}</span>
            <span className="block text-[10px] font-medium uppercase tracking-widest text-ink-subtle">{tApp('tagline')}</span>
          </span>
        </Link>
      </div>

      <nav aria-label="Main" className="flex-1 overflow-y-auto px-3 py-4">
        <p className="label-xs mb-3 px-3">Workspace</p>
        <ul className="space-y-0.5">
          {workspace.map((item) => (
            <SidebarLink key={item.href} {...item} pathname={pathname} label={t(item.labelKey)} />
          ))}
        </ul>
        {admin.length > 0 && (
          <>
            <p className="label-xs mb-3 mt-8 px-3">Administration</p>
            <ul className="space-y-0.5">
              {admin.map((item) => (
                <SidebarLink key={item.href} {...item} pathname={pathname} label={t(item.labelKey)} />
              ))}
            </ul>
          </>
        )}
      </nav>

      {session?.user && (
        <div className="border-t border-border px-3 py-4">
          <div className="rounded-lg bg-surface px-3 py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-fg">
                {initials(session.user.name ?? session.user.email)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-ink">{session.user.name ?? 'User'}</div>
                <div className="truncate text-[11px] text-ink-muted">{session.user.email}</div>
              </div>
              <button
                onClick={() => void signOut({ callbackUrl: '/login' })}
                className="text-ink-subtle transition-colors hover:text-ink"
                aria-label={t('signOut')}
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

function SidebarLink({
  href,
  icon: Icon,
  pathname,
  label,
}: Pick<NavItem, 'href' | 'icon'> & { pathname: string; label: string }) {
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <li>
      <Link
        href={href}
        aria-current={active ? 'page' : undefined}
        className={cn(
          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
          active ? 'bg-surface text-ink' : 'text-ink-muted hover:bg-surface hover:text-ink',
        )}
      >
        <span className="relative flex h-8 w-8 shrink-0 items-center justify-center">
          <span
            className={cn(
              'absolute inset-0 rounded-md transition-colors',
              active ? 'bg-primary-soft' : 'bg-transparent',
            )}
          />
          <Icon
            size={16}
            className={cn('relative transition-colors', active ? 'text-primary' : 'text-ink-muted')}
            aria-hidden="true"
          />
        </span>
        <span>{label}</span>
      </Link>
    </li>
  );
}

function initials(value: string): string {
  return value
    .split(/[@.\s]/)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .slice(0, 2)
    .join('');
}
