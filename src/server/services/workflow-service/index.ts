import type { Workflow, WorkflowCategory, TriggerType } from '@/lib/validation';

/**
 * Workflow registry — mirrors /legal-automation/workflows/* from FlowStack 2.0.
 * Swap this in-memory registry with a Prisma-backed repository when wiring the
 * real multi-tenant database. The public API (listWorkflows / findWorkflow)
 * stays stable.
 */

interface Seed {
  slug: string;
  name: string;
  category: WorkflowCategory;
  description: string;
  triggerType: TriggerType;
  nodeCount: number;
  active: boolean;
  successRate: number;
  avgDurationMs: number;
  hoursSinceLastRun: number | null;
}

const SEEDS: readonly Seed[] = [
  // Client Lifecycle
  { slug: 'onboarding-main',       name: 'Onboarding — Hauptprozess',      category: 'client-lifecycle', description: 'Mandanten-Erstkontakt bis zur aktiven Akte.',                 triggerType: 'form',     nodeCount: 24, active: true,  successRate: 0.97, avgDurationMs: 8400,  hoursSinceLastRun: 2 },
  { slug: 'onboarding-signature',  name: 'Onboarding — Signatur',          category: 'client-lifecycle', description: 'DocuSign-Integration für Vollmacht und Mandatsvertrag.',      triggerType: 'sub-workflow', nodeCount: 11, active: true, successRate: 0.99, avgDurationMs: 3200, hoursSinceLastRun: 5 },
  { slug: 'onboarding-marketing',  name: 'Onboarding — Marketing-Nurture', category: 'client-lifecycle', description: 'Automatisierte E-Mail-Sequenz für Interessenten.',           triggerType: 'schedule', nodeCount: 9,  active: true,  successRate: 0.95, avgDurationMs: 1800,  hoursSinceLastRun: 24 },
  { slug: 'doc-request-main',      name: 'Dokumentenanforderung',          category: 'client-lifecycle', description: 'Mandant erhält Link, lädt Unterlagen hoch, Ablage in DMS.',  triggerType: 'webhook',  nodeCount: 18, active: true,  successRate: 0.94, avgDurationMs: 6100,  hoursSinceLastRun: 1 },
  { slug: 'doc-request-intake',    name: 'Dokumentenanforderung — Intake', category: 'client-lifecycle', description: 'Formular zur Ermittlung benötigter Unterlagen.',             triggerType: 'form',     nodeCount: 12, active: true,  successRate: 0.98, avgDurationMs: 2400,  hoursSinceLastRun: 8 },
  { slug: 'doc-request-processing',name: 'Dokumentenanforderung — Verarbeitung', category: 'client-lifecycle', description: 'Validierung, OCR, Metadaten-Extraktion.',         triggerType: 'sub-workflow', nodeCount: 15, active: true, successRate: 0.91, avgDurationMs: 11200, hoursSinceLastRun: 1 },
  { slug: 'doc-request-reminder',  name: 'Dokumentenanforderung — Erinnerung', category: 'client-lifecycle', description: 'Tag 3, 7, 14 — höflicher Reminder via Mail.',          triggerType: 'schedule', nodeCount: 7,  active: true,  successRate: 0.99, avgDurationMs: 900,   hoursSinceLastRun: 12 },

  // Deadline & Follow-up
  { slug: 'fristen-pruefung',      name: 'Fristenprüfung',                 category: 'deadline-followup', description: 'Tägliche Prüfung offener Fristen gegen Kalender und Akten.', triggerType: 'schedule', nodeCount: 14, active: true, successRate: 0.99, avgDurationMs: 4200,  hoursSinceLastRun: 0 },
  { slug: 'fristen-erinnerung',    name: 'Fristen — Erinnerung',           category: 'deadline-followup', description: 'T-7 und T-3 Erinnerungen an verantwortliche Sachbearbeiter.', triggerType: 'sub-workflow', nodeCount: 8, active: true, successRate: 1.00, avgDurationMs: 1100, hoursSinceLastRun: 3 },
  { slug: 'fristen-eskalation',    name: 'Fristen — Eskalation',           category: 'deadline-followup', description: 'Eskalation an Partner bei drohender Fristüberschreitung.', triggerType: 'sub-workflow', nodeCount: 10, active: true, successRate: 0.98, avgDurationMs: 1600, hoursSinceLastRun: 18 },
  { slug: 'follow-up-main',        name: 'Follow-up — Hauptprozess',       category: 'deadline-followup', description: 'Koordiniert Erinnerungen, Eskalationen und Rückmeldungen.', triggerType: 'schedule', nodeCount: 16, active: true, successRate: 0.96, avgDurationMs: 5400,  hoursSinceLastRun: 1 },
  { slug: 'follow-up-escalation',  name: 'Follow-up — Eskalation',         category: 'deadline-followup', description: 'Stufenweise Eskalation nach fehlender Reaktion.',           triggerType: 'sub-workflow', nodeCount: 9, active: true, successRate: 0.97, avgDurationMs: 1800, hoursSinceLastRun: 6 },
  { slug: 'follow-up-error-handler',name: 'Follow-up — Error Handler',     category: 'deadline-followup', description: 'Auffangen fehlgeschlagener Follow-up-Schritte.',            triggerType: 'error',    nodeCount: 6,  active: true,  successRate: 1.00, avgDurationMs: 400,   hoursSinceLastRun: 48 },
  { slug: 'noshow-detection',      name: 'No-Show-Erkennung',              category: 'deadline-followup', description: 'Erkennt versäumte Termine via Kalender-Sync.',              triggerType: 'schedule', nodeCount: 11, active: true,  successRate: 0.93, avgDurationMs: 2800,  hoursSinceLastRun: 4 },
  { slug: 'noshow-response',       name: 'No-Show-Reaktion',               category: 'deadline-followup', description: 'Automatische Reaktion bei erkanntem No-Show.',              triggerType: 'sub-workflow', nodeCount: 8, active: true, successRate: 0.95, avgDurationMs: 1300, hoursSinceLastRun: 16 },

  // Review & Reporting
  { slug: 'review-intake',         name: 'Review — Intake',                category: 'review-reporting',  description: 'Anfragen aus Bewertungsportalen und Mail erfassen.',        triggerType: 'email',    nodeCount: 10, active: true,  successRate: 0.96, avgDurationMs: 2100,  hoursSinceLastRun: 9 },
  { slug: 'review-response',       name: 'Review — Antwort',               category: 'review-reporting',  description: 'KI-gestützte Antwort-Generierung mit Freigabe-Workflow.',  triggerType: 'sub-workflow', nodeCount: 14, active: false, successRate: 0.88, avgDurationMs: 7400, hoursSinceLastRun: 72 },
  { slug: 'review-optimized',      name: 'Review — Optimiert',             category: 'review-reporting',  description: 'Performance-optimierte Variante mit Batching.',             triggerType: 'schedule', nodeCount: 12, active: true,  successRate: 0.99, avgDurationMs: 3100,  hoursSinceLastRun: 2 },
  { slug: 'bericht-datensammlung', name: 'Bericht — Datensammlung',        category: 'review-reporting',  description: 'Aggregiert KPIs aus CRM, Billing und Zeitrfassung.',       triggerType: 'schedule', nodeCount: 22, active: true,  successRate: 0.94, avgDurationMs: 14200, hoursSinceLastRun: 24 },
  { slug: 'bericht-intern',        name: 'Bericht — Intern',               category: 'review-reporting',  description: 'Wöchentliche Management-Reports per Mail.',                 triggerType: 'schedule', nodeCount: 15, active: true,  successRate: 0.98, avgDurationMs: 6200,  hoursSinceLastRun: 48 },
  { slug: 'bericht-extern',        name: 'Bericht — Extern',               category: 'review-reporting',  description: 'Kundenfacing-Reports mit PDF-Export und Versand.',          triggerType: 'schedule', nodeCount: 19, active: true,  successRate: 0.96, avgDurationMs: 9800,  hoursSinceLastRun: 120 },

  // Meeting Protocols
  { slug: 'protokoll-erstellung',  name: 'Protokoll — Erstellung',         category: 'meeting-protocols', description: 'Transkription → Zusammenfassung → Aktions-Items.',          triggerType: 'webhook',  nodeCount: 17, active: true,  successRate: 0.92, avgDurationMs: 24600, hoursSinceLastRun: 6 },
  { slug: 'protokoll-freigabe',    name: 'Protokoll — Freigabe',           category: 'meeting-protocols', description: 'Workflow für Review und Freigabe durch Teilnehmer.',       triggerType: 'sub-workflow', nodeCount: 9, active: true, successRate: 0.97, avgDurationMs: 1900, hoursSinceLastRun: 14 },
  { slug: 'protokoll-aufgaben',    name: 'Protokoll — Aufgaben',           category: 'meeting-protocols', description: 'Extrahiert Action-Items und legt sie als Tasks an.',        triggerType: 'sub-workflow', nodeCount: 11, active: true, successRate: 0.90, avgDurationMs: 3400, hoursSinceLastRun: 8 },
  { slug: 'approval-subprocess',   name: 'Freigabe — Subprozess',          category: 'meeting-protocols', description: 'Generischer Freigabe-Baustein mit Rollen-Routing.',         triggerType: 'sub-workflow', nodeCount: 8, active: true, successRate: 0.99, avgDurationMs: 800, hoursSinceLastRun: 4 },

  // Triage & Error Handling
  { slug: 'triage-main',           name: 'Eingangs-Triage',                category: 'triage-error-handling', description: 'Klassifiziert eingehende Mails, leitet an zuständige Workflows.', triggerType: 'email', nodeCount: 20, active: true, successRate: 0.89, avgDurationMs: 3700, hoursSinceLastRun: 0 },
  { slug: 'error-handler',         name: 'Zentraler Error-Handler',        category: 'triage-error-handling', description: 'Fängt Fehler aller Workflows ab, protokolliert, alarmiert.', triggerType: 'error',  nodeCount: 12, active: true, successRate: 1.00, avgDurationMs: 600, hoursSinceLastRun: 6 },
];

function isoMinus(hours: number): string {
  return new Date(Date.now() - hours * 3600_000).toISOString();
}

export async function listWorkflows(): Promise<readonly Workflow[]> {
  return SEEDS.map((s) => ({
    slug: s.slug,
    name: s.name,
    category: s.category,
    description: s.description,
    triggerType: s.triggerType,
    nodeCount: s.nodeCount,
    connectionCount: Math.max(0, s.nodeCount - 1),
    active: s.active,
    lastRunAt: s.hoursSinceLastRun === null ? null : isoMinus(s.hoursSinceLastRun),
    successRate: s.successRate,
    avgDurationMs: s.avgDurationMs,
  }));
}

export async function findWorkflow(slug: string): Promise<Workflow | null> {
  const all = await listWorkflows();
  return all.find((w) => w.slug === slug) ?? null;
}
