import type { UserRole } from './validation';

/**
 * Permission matrix — FlowStack role model (Admin/Write/Read).
 * Add new capabilities here; do not inline role strings anywhere else.
 */
export const PERMISSIONS = {
  // Workflows
  'workflows.read':    ['admin', 'write', 'read'],
  'workflows.execute': ['admin', 'write'],
  'workflows.upload':  ['admin'],
  'workflows.delete':  ['admin'],

  // Executions & tasks
  'executions.read':   ['admin', 'write', 'read'],
  'executions.retry':  ['admin', 'write'],
  'tasks.close':       ['admin', 'write'],

  // Calendar
  'calendar.read':     ['admin', 'write', 'read'],
  'calendar.write':    ['admin', 'write'],

  // Settings & tenant
  'settings.read':     ['admin', 'write', 'read'],
  'settings.write':    ['admin'],
  'tenant.manage':     ['admin'],
  'audit.read':        ['admin', 'write'],

  // Users
  'users.read':        ['admin', 'write'],
  'users.invite':      ['admin'],
  'users.delete':      ['admin'],
} as const satisfies Record<string, readonly UserRole[]>;

export type Permission = keyof typeof PERMISSIONS;

export function can(role: UserRole | undefined, permission: Permission): boolean {
  if (!role) return false;
  return (PERMISSIONS[permission] as readonly UserRole[]).includes(role);
}

export function assertCan(role: UserRole | undefined, permission: Permission): void {
  if (!can(role, permission)) throw new ForbiddenError(permission);
}

export class ForbiddenError extends Error {
  override readonly name = 'ForbiddenError';
  constructor(public readonly permission: Permission) {
    super(`Forbidden: missing permission "${permission}"`);
  }
}
