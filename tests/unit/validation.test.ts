import { describe, it, expect } from 'vitest';
import { loginSchema } from '@/lib/validation';

describe('loginSchema', () => {
  it('accepts valid input and normalizes email', () => {
    const result = loginSchema.safeParse({ email: '  Admin@Example.COM ', password: 'LongEnough1!' });
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.email).toBe('admin@example.com');
  });

  it('rejects short passwords', () => {
    const result = loginSchema.safeParse({ email: 'a@b.co', password: '123' });
    expect(result.success).toBe(false);
  });

  it('rejects malformed email', () => {
    const result = loginSchema.safeParse({ email: 'not-email', password: 'LongEnough1!' });
    expect(result.success).toBe(false);
  });
});
