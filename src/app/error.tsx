'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { logger } from '@/lib/logger';

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations('errors');

  useEffect(() => {
    logger.error('App error boundary triggered', {
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="max-w-md text-center">
        <h1 className="heading-display">{t('pageTitle')}</h1>
        <p className="mt-2 text-sm text-ink-muted">{t('pageBody')}</p>
        <div className="mt-6">
          <Button onClick={reset}>{t('retry')}</Button>
        </div>
      </div>
    </div>
  );
}
