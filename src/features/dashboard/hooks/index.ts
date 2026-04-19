'use client';

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { z } from 'zod';
import {
  workflowSchema,
  executionSchema,
  calendarEventSchema,
  metricsSchema,
  type Workflow,
  type Execution,
  type CalendarEvent,
  type Metrics,
} from '@/lib/validation';

const workflowsResponse = z.object({ workflows: z.array(workflowSchema) });
const executionsResponse = z.object({ executions: z.array(executionSchema) });
const eventsResponse = z.object({ events: z.array(calendarEventSchema) });

async function fetchWorkflows(): Promise<readonly Workflow[]> {
  const { data } = await axios.get('/api/workflows');
  return workflowsResponse.parse(data).workflows;
}
async function fetchExecutions(limit: number): Promise<readonly Execution[]> {
  const { data } = await axios.get('/api/executions', { params: { limit } });
  return executionsResponse.parse(data).executions;
}
async function fetchEvents(days: number): Promise<readonly CalendarEvent[]> {
  const { data } = await axios.get('/api/calendar/events', { params: { days } });
  return eventsResponse.parse(data).events;
}
async function fetchMetrics(): Promise<Metrics> {
  const { data } = await axios.get('/api/metrics');
  return metricsSchema.parse(data);
}

export function useWorkflows() {
  return useQuery({ queryKey: ['workflows'], queryFn: fetchWorkflows, staleTime: 30_000 });
}
export function useExecutions(limit = 50) {
  return useQuery({
    queryKey: ['executions', limit],
    queryFn: () => fetchExecutions(limit),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
}
export function useCalendarEvents(days = 14) {
  return useQuery({
    queryKey: ['calendar', days],
    queryFn: () => fetchEvents(days),
    staleTime: 60_000,
  });
}
export function useMetrics() {
  return useQuery({ queryKey: ['metrics'], queryFn: fetchMetrics, staleTime: 30_000 });
}
