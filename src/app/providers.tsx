'use client';

import { useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import { NextIntlClientProvider, type AbstractIntlMessages } from 'next-intl';
import { Toaster } from 'sonner';

interface ProvidersProps {
  children: ReactNode;
  locale: string;
  messages: AbstractIntlMessages;
}

export function Providers({ children, locale, messages }: ProvidersProps) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 30_000,
          },
        },
      }),
  );

  return (
    <SessionProvider>
      <NextIntlClientProvider locale={locale} messages={messages}>
        <QueryClientProvider client={client}>
          {children}
          <Toaster position="top-right" richColors closeButton />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </SessionProvider>
  );
}
