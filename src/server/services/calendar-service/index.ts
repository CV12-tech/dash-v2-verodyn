import type { CalendarEvent } from '@/lib/validation';

/**
 * Calendar events — would come from Microsoft Graph (/me/calendar/events) in
 * production. For now generates a plausible week of items that cross-reference
 * the workflow slugs, so clicking an event can deep-link into a workflow.
 */

interface Seed {
  subject: string;
  startOffsetHours: number;
  durationMinutes: number;
  location: string | null;
  attendees: Array<{ email: string; name: string }>;
  kind: CalendarEvent['kind'];
  relatedWorkflowSlug: string | null;
}

const SEEDS: readonly Seed[] = [
  { subject: 'Mandantengespräch — Müller GmbH',    startOffsetHours: 2,    durationMinutes: 60,  location: 'Besprechungsraum A',   attendees: [{ email: 'c.weber@kanzlei.de',  name: 'Claudia Weber' }, { email: 't.mueller@mueller-gmbh.de', name: 'Thomas Müller' }], kind: 'meeting',  relatedWorkflowSlug: 'onboarding-main' },
  { subject: 'Frist: Einspruch Az. 12 O 345/25',   startOffsetHours: 28,   durationMinutes: 0,   location: null,                   attendees: [], kind: 'deadline', relatedWorkflowSlug: 'fristen-pruefung' },
  { subject: 'Review — Berichtsversand Q1',        startOffsetHours: 30,   durationMinutes: 30,  location: 'Teams',                attendees: [{ email: 's.braun@kanzlei.de',  name: 'Sandra Braun' }], kind: 'review',   relatedWorkflowSlug: 'bericht-extern' },
  { subject: 'Protokoll-Freigabe — Vorstandssitzung', startOffsetHours: 52, durationMinutes: 45, location: 'Büro Dr. Keller',      attendees: [{ email: 'l.keller@kanzlei.de', name: 'Dr. Lukas Keller' }, { email: 's.braun@kanzlei.de', name: 'Sandra Braun' }], kind: 'protocol', relatedWorkflowSlug: 'protokoll-freigabe' },
  { subject: 'Frist: Stellungnahme Finanzamt',     startOffsetHours: 76,   durationMinutes: 0,   location: null,                   attendees: [], kind: 'deadline', relatedWorkflowSlug: 'fristen-eskalation' },
  { subject: 'Onboarding-Call — Schmidt KG',       startOffsetHours: 96,   durationMinutes: 45,  location: 'Teams',                attendees: [{ email: 'c.weber@kanzlei.de', name: 'Claudia Weber' }, { email: 'info@schmidt-kg.de', name: 'Schmidt KG' }], kind: 'meeting', relatedWorkflowSlug: 'onboarding-main' },
  { subject: 'Partner-Review — Monatsreport',      startOffsetHours: 120,  durationMinutes: 60,  location: 'Konferenzraum',        attendees: [{ email: 'l.keller@kanzlei.de', name: 'Dr. Lukas Keller' }, { email: 'partner2@kanzlei.de', name: 'Dr. Anja Hoffmann' }], kind: 'review', relatedWorkflowSlug: 'bericht-intern' },
  { subject: 'Frist: Berufungsschrift',            startOffsetHours: 148,  durationMinutes: 0,   location: null,                   attendees: [], kind: 'deadline', relatedWorkflowSlug: 'fristen-pruefung' },
  { subject: 'Kanzleitag — Strategie 2027',        startOffsetHours: 168,  durationMinutes: 240, location: 'Konferenzraum groß',    attendees: [{ email: 'alle@kanzlei.de', name: 'Gesamtes Team' }], kind: 'meeting', relatedWorkflowSlug: null },
];

export async function listUpcomingEvents(days = 14): Promise<readonly CalendarEvent[]> {
  const now = Date.now();
  const cutoff = now + days * 24 * 3600_000;

  return SEEDS.map((s, i) => {
    const start = new Date(now + s.startOffsetHours * 3600_000);
    const end = new Date(start.getTime() + s.durationMinutes * 60_000);
    return {
      id: `evt_${String(i + 1).padStart(4, '0')}`,
      subject: s.subject,
      start: start.toISOString(),
      end: end.toISOString(),
      location: s.location,
      attendees: s.attendees,
      kind: s.kind,
      relatedWorkflowSlug: s.relatedWorkflowSlug,
    };
  }).filter((e) => new Date(e.start).getTime() <= cutoff);
}
