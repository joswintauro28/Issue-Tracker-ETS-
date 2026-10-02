import type { BadgeTone } from '../components/ui/Badge';
import type { IssuePriority, IssueStatus } from '../types';

export const STATUS_LABELS: Record<IssueStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  closed: 'Closed',
};

export const STATUS_BADGE_TONES: Record<IssueStatus, BadgeTone> = {
  open: 'blue',
  in_progress: 'amber',
  closed: 'green',
};

export const PRIORITY_LABELS: Record<IssuePriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

export const PRIORITY_BADGE_TONES: Record<IssuePriority, BadgeTone> = {
  low: 'gray',
  medium: 'blue',
  high: 'red',
};

export const STATUS_ORDER: IssueStatus[] = ['open', 'in_progress', 'closed'];
export const PRIORITY_ORDER: IssuePriority[] = ['low', 'medium', 'high'];

/** Solid bar colors for the dashboard status distribution chart. */
export const STATUS_BAR_CLASSES: Record<IssueStatus, string> = {
  open: 'bg-sky-500',
  in_progress: 'bg-amber-500',
  closed: 'bg-emerald-500',
};

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(isoDate: string): string {
  return new Date(isoDate).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
