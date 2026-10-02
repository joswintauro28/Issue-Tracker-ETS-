import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { dashboardApi } from '../api/dashboard';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import PageHeader from '../components/ui/PageHeader';
import {
  PRIORITY_BADGE_TONES,
  PRIORITY_LABELS,
  STATUS_BADGE_TONES,
  STATUS_BAR_CLASSES,
  STATUS_LABELS,
  STATUS_ORDER,
  formatDate,
  formatDateTime,
} from '../lib/issueFormat';
import type { DashboardSummary, IssueStatus } from '../types';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAdmin } = useAuth();

  const loadSummary = useCallback(() => {
    setIsLoading(true);
    dashboardApi
      .summary()
      .then((data) => {
        setSummary(data);
        setError(null);
      })
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
      .finally(() => setIsLoading(false));
  }, []);

  // Fetches on every visit, so counts and lists are always current after
  // creating, editing, assigning, closing or deleting issues elsewhere.
  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const statusCounts: Record<IssueStatus, number> = {
    open: summary?.open_issues ?? 0,
    in_progress: summary?.in_progress_issues ?? 0,
    closed: summary?.closed_issues ?? 0,
  };

  const statCards = [
    { label: 'Total Issues', value: summary?.total_issues ?? 0, accent: 'text-indigo-600' },
    { label: 'Open', value: statusCounts.open, accent: 'text-sky-600' },
    { label: 'In Progress', value: statusCounts.in_progress, accent: 'text-amber-600' },
    { label: 'Closed', value: statusCounts.closed, accent: 'text-emerald-600' },
  ];

  return (
    <div>
      <PageHeader
        title={isAdmin ? 'Dashboard' : 'My tasks'}
        description={
          isAdmin
            ? 'Live overview of issue activity, computed from the database.'
            : 'Live overview of your assigned tasks, computed from the database.'
        }
        actions={
          <Button variant="secondary" onClick={loadSummary} isLoading={isLoading}>
            Refresh
          </Button>
        }
      />

      {error && (
        <div
          className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          <span>{error}</span>
          <Button variant="secondary" size="sm" onClick={loadSummary}>
            Retry
          </Button>
        </div>
      )}

      {isLoading && !summary ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
            aria-hidden="true"
          />
          Loading dashboard…
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Statistic cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {statCards.map((card) => (
              <Card key={card.label} bodyClassName="p-5">
                <p className="text-sm font-medium text-slate-500">{card.label}</p>
                <p className={`mt-2 text-3xl font-bold ${card.accent}`}>{card.value}</p>
              </Card>
            ))}
          </div>

          {/* Status distribution */}
          <Card title="Status distribution">
            {summary.total_issues === 0 ? (
              <p className="text-sm text-slate-500">
                No issues yet — the distribution appears once issues are created.
              </p>
            ) : (
              <div className="space-y-4">
                {STATUS_ORDER.map((status) => {
                  const count = statusCounts[status];
                  const percentage = Math.round((count / summary.total_issues) * 100);
                  return (
                    <div key={status}>
                      <div className="mb-1 flex items-center justify-between text-xs font-medium text-slate-500">
                        <span>{STATUS_LABELS[status]}</span>
                        <span>
                          {count} {count === 1 ? 'issue' : 'issues'} · {percentage}%
                        </span>
                      </div>
                      <div
                        className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100"
                        role="img"
                        aria-label={`${STATUS_LABELS[status]}: ${count} of ${summary.total_issues} issues`}
                      >
                        <div
                          className={`h-full rounded-full ${STATUS_BAR_CLASSES[status]}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Recent issues */}
          <Card title="Recent issues" bodyClassName="p-0">
            {summary.recent_issues.length === 0 ? (
              <div className="p-10 text-center">
                <p className="text-sm font-medium text-slate-900">
                  {isAdmin ? 'No issues yet.' : 'No tasks assigned to you.'}
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  {isAdmin ? (
                    <>
                      Create the first one from the{' '}
                      <Link to="/issues" className="font-semibold text-indigo-600">
                        Issues page
                      </Link>
                      .
                    </>
                  ) : (
                    'Tasks assigned to you by an admin will appear here.'
                  )}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Title</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3">Reporter</th>
                      <th className="px-5 py-3">Assignee</th>
                      <th className="px-5 py-3">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {summary.recent_issues.map((issue) => (
                      <tr key={issue.id} className="transition hover:bg-slate-50">
                        <td className="max-w-xs px-5 py-3 font-medium text-slate-900">
                          <Link to={`/issues/${issue.id}`} className="hover:text-indigo-600">
                            #{issue.id} · {issue.title}
                          </Link>
                        </td>
                        <td className="px-5 py-3">
                          <Badge tone={STATUS_BADGE_TONES[issue.status]}>
                            {STATUS_LABELS[issue.status]}
                          </Badge>
                        </td>
                        <td className="px-5 py-3 text-slate-600">{issue.reporter.name}</td>
                        <td className="px-5 py-3 text-slate-600">
                          {issue.assignee?.name ?? 'Unassigned'}
                        </td>
                        <td className="px-5 py-3 text-slate-500">{formatDate(issue.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* My assigned issues */}
          <Card title="My assigned issues" bodyClassName="p-0">
            {summary.my_assigned_issues.length === 0 ? (
              <p className="p-5 text-sm text-slate-500">
                Nothing is assigned to you right now.
              </p>
            ) : (
              <ul className="divide-y divide-slate-200">
                {summary.my_assigned_issues.map((issue) => (
                  <li key={issue.id}>
                    <Link
                      to={`/issues/${issue.id}`}
                      className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 transition hover:bg-slate-50"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-900">
                          #{issue.id} · {issue.title}
                        </p>
                        <p className="text-xs text-slate-500">
                          Reported by {issue.reporter.name} · updated{' '}
                          {formatDateTime(issue.updated_at)}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <Badge tone={PRIORITY_BADGE_TONES[issue.priority]}>
                          {PRIORITY_LABELS[issue.priority]}
                        </Badge>
                        <Badge tone={STATUS_BADGE_TONES[issue.status]}>
                          {STATUS_LABELS[issue.status]}
                        </Badge>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      ) : null}
    </div>
  );
}
