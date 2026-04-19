'use client';

import { useState, type FormEvent } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { loginSchema } from '@/lib/validation';

type FieldErrors = Partial<Record<'email' | 'password', string>>;

export default function LoginPage() {
  const t = useTranslations('auth.login');
  const tErr = useTranslations('auth.errors');
  const tApp = useTranslations('app');
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/overview';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErrors({});

    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      const next: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        const field = issue.path[0];
        if (field === 'email' || field === 'password') {
          try {
            next[field] = tErr(issue.message as 'invalidEmail' | 'passwordTooShort' | 'passwordTooLong');
          } catch {
            next[field] = issue.message;
          }
        }
      }
      setErrors(next);
      return;
    }

    setSubmitting(true);
    try {
      const res = await signIn('credentials', {
        email: parsed.data.email,
        password: parsed.data.password,
        redirect: false,
      });
      if (!res || res.error) {
        toast.error(tErr('invalidCredentials'));
        setSubmitting(false);
        return;
      }
      router.push(callbackUrl);
      router.refresh();
    } catch {
      toast.error(tErr('generic'));
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm animate-slide-up">
        <div className="mb-8 flex flex-col items-center">
          <span className="relative mb-4 flex h-12 w-12 items-center justify-center">
            <span className="absolute inset-0 rounded-lg bg-primary-soft" />
            <svg className="relative text-primary" width="26" height="26" viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 12 L16 6 L24 12 L24 20 L16 26 L8 20 Z" />
              <circle cx="16" cy="16" r="3" fill="currentColor" />
            </svg>
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-ink">{tApp('name')}</h1>
          <p className="mt-0.5 text-[11px] font-medium uppercase tracking-widest text-ink-subtle">
            {tApp('tagline')}
          </p>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-ink">{t('title')}</h2>
              <p className="mt-1 text-sm text-ink-muted">{t('subtitle')}</p>
            </div>

            <form onSubmit={onSubmit} noValidate className="space-y-4">
              <Input
                label={t('email')}
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={errors.email}
              />
              <Input
                label={t('password')}
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={errors.password}
              />
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? t('submitting') : t('submit')}
              </Button>
            </form>

            <p className="mt-4 rounded-md bg-surface-muted px-3 py-2 text-center text-xs text-ink-muted">
              {t('demoHint')}
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
