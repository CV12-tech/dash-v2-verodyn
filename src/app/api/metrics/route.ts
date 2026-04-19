import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/server/auth/config';
import { can } from '@/lib/rbac';
import { getMetrics } from '@/server/services/metrics-service';

export async function GET(): Promise<NextResponse> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!can(session.user.role, 'workflows.read')) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  const metrics = await getMetrics();
  return NextResponse.json(metrics, { headers: { 'Cache-Control': 'private, max-age=30' } });
}
