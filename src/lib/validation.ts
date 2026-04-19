import { z } from 'zod';

// ── Auth ──────────────────────────────────────────────────────────────────
export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email('auth.errors.invalidEmail'),
  password: z.string().min(8, 'auth.errors.passwordTooShort').max(128, 'auth.errors.passwordTooLong'),
});
export type LoginInput = z.infer<typeof loginSchema>;

// ── Roles — FlowStack model ───────────────────────────────────────────────
export const userRoleSchema = z.enum(['admin', 'write', 'read']);
export type UserRole = z.infer<typeof userRoleSchema>;

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  role: userRoleSchema,
  createdAt: z.string().datetime(),
});
export type User = z.infer<typeof userSchema>;

// ── Workflows ─────────────────────────────────────────────────────────────
export const workflowCategorySchema = z.enum([
  'client-lifecycle',
  'deadline-followup',
  'review-reporting',
  'meeting-protocols',
  'triage-error-handling',
]);
export type WorkflowCategory = z.infer<typeof workflowCategorySchema>;

export const triggerTypeSchema = z.enum([
  'webhook', 'schedule', 'form', 'email', 'error', 'sub-workflow', 'unknown',
]);
export type TriggerType = z.infer<typeof triggerTypeSchema>;

export const workflowSchema = z.object({
  slug: z.string(),
  name: z.string(),
  category: workflowCategorySchema,
  description: z.string(),
  triggerType: triggerTypeSchema,
  nodeCount: z.number().int().nonnegative(),
  connectionCount: z.number().int().nonnegative(),
  active: z.boolean(),
  lastRunAt: z.string().datetime().nullable(),
  successRate: z.number().min(0).max(1),
  avgDurationMs: z.number().nonnegative(),
});
export type Workflow = z.infer<typeof workflowSchema>;

// ── Executions ────────────────────────────────────────────────────────────
export const executionStatusSchema = z.enum(['pending', 'running', 'success', 'error', 'cancelled']);
export type ExecutionStatus = z.infer<typeof executionStatusSchema>;

export const executionSchema = z.object({
  id: z.string(),
  workflowSlug: z.string(),
  workflowName: z.string(),
  status: executionStatusSchema,
  startedAt: z.string().datetime(),
  completedAt: z.string().datetime().nullable(),
  durationMs: z.number().nonnegative().nullable(),
  triggeredBy: z.string(),
  errorMessage: z.string().nullable(),
});
export type Execution = z.infer<typeof executionSchema>;

// ── Calendar events (Microsoft 365) ───────────────────────────────────────
export const calendarEventSchema = z.object({
  id: z.string(),
  subject: z.string(),
  start: z.string().datetime(),
  end: z.string().datetime(),
  location: z.string().nullable(),
  attendees: z.array(z.object({ email: z.string(), name: z.string() })),
  kind: z.enum(['meeting', 'deadline', 'review', 'protocol']),
  relatedWorkflowSlug: z.string().nullable(),
});
export type CalendarEvent = z.infer<typeof calendarEventSchema>;

// ── Aggregate metrics for overview page ───────────────────────────────────
export const metricsSchema = z.object({
  activeWorkflows:   z.object({ value: z.number(), changePercent: z.number() }),
  executions24h:     z.object({ value: z.number(), changePercent: z.number() }),
  successRate:       z.object({ value: z.number(), changePercent: z.number() }), // 0..1
  upcomingDeadlines: z.object({ value: z.number(), changePercent: z.number() }),
  timeseries: z.array(z.object({
    date: z.string(),
    executions: z.number(),
    successes: z.number(),
  })),
});
export type Metrics = z.infer<typeof metricsSchema>;
