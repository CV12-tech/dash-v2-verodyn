import Link from 'next/link';
import { getTranslations } from 'next-intl/server';

export default async function NotFound() {
  const t = await getTranslations('errors');
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="max-w-md text-center">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-subtle">404</p>
        <h1 className="heading-display mt-2">{t('notFoundTitle')}</h1>
        <p className="mt-2 text-sm text-ink-muted">{t('notFoundBody')}</p>
        <Link
          href="/overview"
          className="mt-6 inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-fg hover:bg-primary/90"
        >
          {t('backHome')}
        </Link>
      </div>
    </div>
  );
}
