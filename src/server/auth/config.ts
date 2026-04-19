import type { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';

import { env } from '@/lib/env';
import { logger } from '@/lib/logger';
import { loginSchema, userRoleSchema, type UserRole } from '@/lib/validation';
import { findUserByEmail } from '@/server/services/user-service';

export const authOptions: NextAuthOptions = {
  secret: env.NEXTAUTH_SECRET,
  session: { strategy: 'jwt', maxAge: 8 * 60 * 60 /* 8h */ },
  pages: { signIn: '/login', error: '/login' },
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const parsed = loginSchema.safeParse(credentials);
        if (!parsed.success) {
          logger.warn('Login attempt with invalid payload');
          return null;
        }

        const user = await findUserByEmail(parsed.data.email);
        if (!user) {
          // Constant-time fake compare to mitigate user-enumeration timing attacks
          await bcrypt.compare(parsed.data.password, '$2a$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinvali');
          logger.warn('Login attempt for unknown user', { email: parsed.data.email });
          return null;
        }

        const ok = await bcrypt.compare(parsed.data.password, user.passwordHash);
        if (!ok) {
          logger.warn('Login failed: bad password', { userId: user.id });
          return null;
        }

        logger.info('Login success', { userId: user.id });
        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const roleParsed = userRoleSchema.safeParse((user as { role?: unknown }).role);
        token.role = roleParsed.success ? roleParsed.data : 'read';
        token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = (token.userId as string | undefined) ?? '';
        session.user.role = (token.role as UserRole | undefined) ?? 'read';
      }
      return session;
    },
  },
  events: {
    signOut({ token }) {
      logger.info('Sign out', { userId: token.userId });
    },
  },
};
