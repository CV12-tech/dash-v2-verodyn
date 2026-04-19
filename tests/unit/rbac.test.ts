import { describe, it, expect } from 'vitest';
import { can, assertCan, ForbiddenError } from '@/lib/rbac';

describe('rbac.can', () => {
  it('grants admin all workflow capabilities', () => {
    expect(can('admin', 'workflows.read')).toBe(true);
    expect(can('admin', 'workflows.execute')).toBe(true);
    expect(can('admin', 'workflows.upload')).toBe(true);
    expect(can('admin', 'workflows.delete')).toBe(true);
  });

  it('restricts read role to read-only operations', () => {
    expect(can('read', 'workflows.read')).toBe(true);
    expect(can('read', 'executions.read')).toBe(true);
    expect(can('read', 'calendar.read')).toBe(true);
    expect(can('read', 'workflows.execute')).toBe(false);
    expect(can('read', 'workflows.upload')).toBe(false);
    expect(can('read', 'workflows.delete')).toBe(false);
    expect(can('read', 'settings.write')).toBe(false);
    expect(can('read', 'tenant.manage')).toBe(false);
  });

  it('permits write role to execute and edit but not manage tenant', () => {
    expect(can('write', 'workflows.execute')).toBe(true);
    expect(can('write', 'executions.retry')).toBe(true);
    expect(can('write', 'calendar.write')).toBe(true);
    expect(can('write', 'tasks.close')).toBe(true);
    expect(can('write', 'audit.read')).toBe(true);
    expect(can('write', 'workflows.upload')).toBe(false);
    expect(can('write', 'workflows.delete')).toBe(false);
    expect(can('write', 'tenant.manage')).toBe(false);
    expect(can('write', 'users.invite')).toBe(false);
  });

  it('denies everything for undefined role', () => {
    expect(can(undefined, 'workflows.read')).toBe(false);
    expect(can(undefined, 'calendar.read')).toBe(false);
  });
});

describe('rbac.assertCan', () => {
  it('throws ForbiddenError when permission missing', () => {
    expect(() => assertCan('read', 'workflows.delete')).toThrow(ForbiddenError);
  });

  it('does not throw when permission granted', () => {
    expect(() => assertCan('admin', 'workflows.delete')).not.toThrow();
  });

  it('ForbiddenError carries the offending permission', () => {
    try {
      assertCan('read', 'workflows.upload');
      expect.fail('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ForbiddenError);
      expect((err as ForbiddenError).permission).toBe('workflows.upload');
    }
  });
});
