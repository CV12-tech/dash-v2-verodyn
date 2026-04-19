import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/server/auth/config';
import { can } from '@/lib/rbac';
import { listExecutions } from '@/server/services/execution-service';

export async function GET(req: Request): Promise<NextResponse> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!can(session.user.role, 'executions.read')) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { searchParams } = new URL(req.url);
  const limit = Math.min(200, Math.max(1, Number(searchParams.get('limit') ?? 50)));
  const executions = await listExecutions(limit);
  return NextResponse.json({ executions });
}
