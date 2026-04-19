import type { Execution, ExecutionStatus } from '@/lib/validation';

/**
 * Mock execution history. Swap with a Prisma query on WorkflowExecution
 * when the real DB is wired. Deterministic so charts stay stable across reloads.
 */

interface Seed {
  workflowSlug: string;
  workflowName: string;
  status: ExecutionStatus;
  minutesAgo: number;
  durationMs: number | null;
  triggeredBy: string;
  errorMessage?: string;
}

const SEEDS: readonly Seed[] = [
  { workflowSlug: 'fristen-pruefung',       workflowName: 'Fristenprüfung',                status: 'success', minutesAgo: 12,   durationMs: 4200,  triggeredBy: 'schedule' },
  { workflowSlug: 'triage-main',            workflowName: 'Eingangs-Triage',               status: 'running', minutesAgo: 2,    durationMs: null,  triggeredBy: 'email:inbox@kanzlei.de' },
  { workflowSlug: 'doc-request-main',       workflowName: 'Dokumentenanforderung',         status: 'success', minutesAgo: 38,   durationMs: 6100,  triggeredBy: 'webhook' },
  { workflowSlug: 'onboarding-main',        workflowName: 'Onboarding — Hauptprozess',     status: 'success', minutesAgo: 124,  durationMs: 8400,  triggeredBy: 'form:web' },
  { workflowSlug: 'protokoll-erstellung',   workflowName: 'Protokoll — Erstellung',        status: 'error',   minutesAgo: 360,  durationMs: 19200, triggeredBy: 'webhook:teams', errorMessage: 'OpenAI API: rate_limit_exceeded' },
  { workflowSlug: 'fristen-eskalation',     workflowName: 'Fristen — Eskalation',          status: 'success', minutesAgo: 1080, durationMs: 1600,  triggeredBy: 'sub-workflow' },
  { workflowSlug: 'noshow-detection',       workflowName: 'No-Show-Erkennung',             status: 'success', minutesAgo: 240,  durationMs: 2800,  triggeredBy: 'schedule' },
  { workflowSlug: 'review-response',        workflowName: 'Review — Antwort',              status: 'error',   minutesAgo: 4320, durationMs: 7400,  triggeredBy: 'sub-workflow', errorMessage: 'Approval timeout after 24h' },
  { workflowSlug: 'bericht-datensammlung',  workflowName: 'Bericht — Datensammlung',       status: 'success', minutesAgo: 1440, durationMs: 14200, triggeredBy: 'schedule' },
  { workflowSlug: 'doc-request-reminder',   workflowName: 'Dokumentenanforderung — Erinnerung', status: 'success', minutesAgo: 720, durationMs: 900, triggeredBy: 'schedule' },
  { workflowSlug: 'follow-up-main',         workflowName: 'Follow-up — Hauptprozess',      status: 'success', minutesAgo: 60,   durationMs: 5400,  triggeredBy: 'schedule' },
  { workflowSlug: 'onboarding-signature',   workflowName: 'Onboarding — Signatur',         status: 'success', minutesAgo: 300,  durationMs: 3200,  triggeredBy: 'sub-workflow' },
  { workflowSlug: 'protokoll-aufgaben',     workflowName: 'Protokoll — Aufgaben',          status: 'success', minutesAgo: 480,  durationMs: 3400,  triggeredBy: 'sub-workflow' },
  { workflowSlug: 'error-handler',          workflowName: 'Zentraler Error-Handler',       status: 'success', minutesAgo: 360,  durationMs: 600,   triggeredBy: 'error' },
  { workflowSlug: 'review-intake',          workflowName: 'Review — Intake',               status: 'success', minutesAgo: 540,  durationMs: 2100,  triggeredBy: 'email:reviews' },
  { workflowSlug: 'triage-main',            workflowName: 'Eingangs-Triage',               status: 'error',   minutesAgo: 180,  durationMs: 3700,  triggeredBy: 'email:inbox@kanzlei.de', errorMessage: 'Classifier returned low confidence (<0.6)' },
  { workflowSlug: 'doc-request-intake',     workflowName: 'Dokumentenanforderung — Intake',status: 'success', minutesAgo: 480,  durationMs: 2400,  triggeredBy: 'form:web' },
  { workflowSlug: 'fristen-erinnerung',     workflowName: 'Fristen — Erinnerung',          status: 'success', minutesAgo: 180,  durationMs: 1100,  triggeredBy: 'sub-workflow' },
  { workflowSlug: 'bericht-intern',         workflowName: 'Bericht — Intern',              status: 'success', minutesAgo: 2880, durationMs: 6200,  triggeredBy: 'schedule' },
  { workflowSlug: 'onboarding-marketing',   workflowName: 'Onboarding — Marketing-Nurture',status: 'success', minutesAgo: 1440, durationMs: 1800,  triggeredBy: 'schedule' },
  { workflowSlug: 'review-optimized',       workflowName: 'Review — Optimiert',            status: 'success', minutesAgo: 120,  durationMs: 3100,  triggeredBy: 'schedule' },
  { workflowSlug: 'approval-subprocess',    workflowName: 'Freigabe — Subprozess',         status: 'success', minutesAgo: 240,  durationMs: 800,   triggeredBy: 'sub-workflow' },
  { workflowSlug: 'noshow-response',        workflowName: 'No-Show-Reaktion',              status: 'success', minutesAgo: 960,  durationMs: 1300,  triggeredBy: 'sub-workflow' },
  { workflowSlug: 'doc-request-processing', workflowName: 'Dokumentenanforderung — Verarbeitung', status: 'success', minutesAgo: 90, durationMs: 11200, triggeredBy: 'sub-workflow' },
];

function isoMinus(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

export async function listExecutions(limit = 50): Promise<readonly Execution[]> {
  return SEEDS.slice(0, limit).map((s, i) => {
    const startedAt = isoMinus(s.minutesAgo);
    const completedAt =
      s.status === 'running' || s.status === 'pending' || s.durationMs === null
        ? null
        : new Date(new Date(startedAt).getTime() + s.durationMs).toISOString();
    return {
      id: `exec_${String(i + 1).padStart(5, '0')}`,
      workflowSlug: s.workflowSlug,
      workflowName: s.workflowName,
      status: s.status,
      startedAt,
      completedAt,
      durationMs: s.durationMs,
      triggeredBy: s.triggeredBy,
      errorMessage: s.errorMessage ?? null,
    };
  });
}

export async function listExecutionsByWorkflow(slug: string, limit = 20): Promise<readonly Execution[]> {
  const all = await listExecutions(1000);
  return all.filter((e) => e.workflowSlug === slug).slice(0, limit);
}
