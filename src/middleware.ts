import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';

const ROUTE_ROLES: ReadonlyArray<{ prefix: string; allowed: ReadonlyArray<string> }> = [
  { prefix: '/settings', allowed: ['admin'] },
];

export default withAuth(
  function middleware(req) {
    const role = req.nextauth.token?.role as string | undefined;
    const path = req.nextUrl.pathname;
    for (const rule of ROUTE_ROLES) {
      if (path.startsWith(rule.prefix) && (!role || !rule.allowed.includes(role))) {
        const url = req.nextUrl.clone();
        url.pathname = '/overview';
        url.searchParams.set('forbidden', rule.prefix);
        return NextResponse.redirect(url);
      }
    }
    return NextResponse.next();
  },
  {
    callbacks: { authorized: ({ token }) => !!token },
    pages: { signIn: '/login' },
  },
);

export const config = {
  matcher: ['/overview/:path*', '/workflows/:path*', '/executions/:path*', '/calendar/:path*', '/tasks/:path*', '/settings/:path*'],
};
