import bcrypt from 'bcryptjs';
import type { UserRole } from '@/lib/validation';

export interface UserRecord {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  passwordHash: string;
  createdAt: string;
}

const DEMO_PASSWORD_HASH = bcrypt.hashSync('ChangeMe!2025', 12);

const USERS: readonly UserRecord[] = [
  { id: 'usr_001', email: 'admin@verodyn.local',  name: 'Admin Demo', role: 'admin', passwordHash: DEMO_PASSWORD_HASH, createdAt: '2025-01-01T00:00:00.000Z' },
  { id: 'usr_002', email: 'write@verodyn.local',  name: 'Write Demo', role: 'write', passwordHash: DEMO_PASSWORD_HASH, createdAt: '2025-01-02T00:00:00.000Z' },
  { id: 'usr_003', email: 'read@verodyn.local',   name: 'Read Demo',  role: 'read',  passwordHash: DEMO_PASSWORD_HASH, createdAt: '2025-01-03T00:00:00.000Z' },
];

export async function findUserByEmail(email: string): Promise<UserRecord | null> {
  const normalized = email.trim().toLowerCase();
  return USERS.find((u) => u.email === normalized) ?? null;
}

export async function findUserById(id: string): Promise<UserRecord | null> {
  return USERS.find((u) => u.id === id) ?? null;
}

export async function listUsers(): Promise<ReadonlyArray<Omit<UserRecord, 'passwordHash'>>> {
  return USERS.map(({ passwordHash: _pw, ...rest }) => rest);
}
