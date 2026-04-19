import { getRequestConfig } from 'next-intl/server';
import { cookies } from 'next/headers';
import { DEFAULT_LOCALE, LOCALES, type Locale } from './config';

export default getRequestConfig(async () => {
  const cookieLocale = cookies().get('NEXT_LOCALE')?.value;
  const locale: Locale =
    cookieLocale && (LOCALES as readonly string[]).includes(cookieLocale)
      ? (cookieLocale as Locale)
      : DEFAULT_LOCALE;

  const messages = (await import(`./messages/${locale}.json`)).default;
  return { locale, messages };
});
