import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { issuesApi } from '../api/issues';
import { getApiErrorMessage } from '../api/client';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import PageHeader from '../components/ui/PageHeader';
import { STATUS_BADGE_TONES, STATUS_LABELS, formatDate } from '../lib/issueFormat';
import type { Issue, IssueStatus } from '../types';

const STATUS_ORDER: IssueStatus[] = ['open', 'in_progress', 'closed'];

export default function DashboardPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    issuesApi
      .list()
      .then(setIssues)
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
      .finally(() => setIsLoading(false));
  }, []);

  const counts: Record<IssueStatus, number> = {
    open: issues.filter((issue) => issue.status === 'open').length,
    in_progress: issues.filter((issue) => issue.status === 'in_progress').length,
    closed: issues.filter((issue) => issue.status === 'closed').length,
  };

  const recentIssues = issues.slice(0, 5);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of issue activity across the project."
        actions={
          <Link to="/issues">
            <Button>View all issues</Button>
          </Link>
        }
      />

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {isLoading ? (
        <Card>
          <p className="text-sm text-slate-500">Loading dashboard…</p>
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            {STATUS_ORDER.map((status) => (
              <Card key={status} bodyClassName="p-5">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-500">{STATUS_LABELS[status]}</p>
                  <Badge tone={STATUS_BADGE_TONES[status]}>{STATUS_LABELS[status]}</Badge>
                </div>
                <p className="mt-2 text-3xl font-bold text-slate-900">{counts[status]}</p>
              </Card>
            ))}
          </div>

          <Card title="Recent issues" bodyClassName="p-0">
            {recentIssues.length === 0 ? (
              <p className="p-5 text-sm text-slate-500">
                No issues yet. Head to the Issues page to create the first one.
              </p>
            ) : (
              <ul className="divide-y divide-slate-200">
                {recentIssues.map((issue) => (
                  <li key={issue.id}>
                    <Link
                      to={`/issues/${issue.id}`}
                      className="flex items-center justify-between gap-4 px-5 py-3 transition hover:bg-slate-50"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-900">
                          #{issue.id} · {issue.title}
                        </p>
                        <p className="text-xs text-slate-500">
                          {issue.reporter.name} · {formatDate(issue.created_at)}
                        </p>
                      </div>
                      <Badge tone={STATUS_BADGE_TONES[issue.status]}>
                        {STATUS_LABELS[issue.status]}
                      </Badge>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
