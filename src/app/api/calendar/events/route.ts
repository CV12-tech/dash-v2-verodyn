import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/server/auth/config';
import { can } from '@/lib/rbac';
import { listUpcomingEvents } from '@/server/services/calendar-service';

export async function GET(req: Request): Promise<NextResponse> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!can(session.user.role, 'calendar.read')) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { searchParams } = new URL(req.url);
  const days = Math.min(60, Math.max(1, Number(searchParams.get('days') ?? 14)));
  const events = await listUpcomingEvents(days);
  return NextResponse.json({ events });
}
