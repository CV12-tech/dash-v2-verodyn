import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/server/auth/config';
import { can } from '@/lib/rbac';
import { listWorkflows } from '@/server/services/workflow-service';

export async function GET(): Promise<NextResponse> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!can(session.user.role, 'workflows.read')) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  const workflows = await listWorkflows();
  return NextResponse.json({ workflows }, { headers: { 'Cache-Control': 'private, max-age=30' } });
}
