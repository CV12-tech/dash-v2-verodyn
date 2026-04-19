import 'next-auth';
import 'next-auth/jwt';
import type { UserRole } from '@/lib/validation';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      email: string;
      name?: string | null;
      role: UserRole;
    };
  }

  interface User {
    id: string;
    email: string;
    name?: string | null;
    role: UserRole;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    userId?: string;
    role?: UserRole;
  }
}
