import type { WorkflowCategory } from '@/lib/validation';

/**
 * FlowStack workflow taxonomy.
 * Colors reference design tokens so they switch with theme and remain accessible.
 */
export interface CategoryMeta {
  slug: WorkflowCategory;
  labelDe: string;
  labelEn: string;
  description: string;
  token: 'primary' | 'success' | 'warning' | 'info';
}

export const CATEGORIES: readonly CategoryMeta[] = [
  {
    slug: 'client-lifecycle',
    labelDe: 'Mandanten-Lifecycle',
    labelEn: 'Client lifecycle',
    description: 'Onboarding, Signatur, Dokumentenanforderung, Marketing-Nurture',
    token: 'primary',
  },
  {
    slug: 'deadline-followup',
    labelDe: 'Fristen & Follow-up',
    labelEn: 'Deadlines & follow-up',
    description: 'Fristenprüfung, Eskalation, Erinnerungen, No-Show-Erkennung',
    token: 'warning',
  },
  {
    slug: 'review-reporting',
    labelDe: 'Review & Reporting',
    labelEn: 'Review & reporting',
    description: 'Berichte intern/extern, Datensammlung, Review-Response',
    token: 'info',
  },
  {
    slug: 'meeting-protocols',
    labelDe: 'Meeting-Protokolle',
    labelEn: 'Meeting protocols',
    description: 'Protokollerstellung, Freigaben, Aufgaben-Extraktion',
    token: 'success',
  },
  {
    slug: 'triage-error-handling',
    labelDe: 'Triage & Error-Handling',
    labelEn: 'Triage & error handling',
    description: 'Eingangs-Triage, zentrale Error-Handler, Sub-Workflows',
    token: 'warning',
  },
] as const;

export const CATEGORY_BY_SLUG: Record<WorkflowCategory, CategoryMeta> = Object.fromEntries(
  CATEGORIES.map((c) => [c.slug, c]),
) as Record<WorkflowCategory, CategoryMeta>;
