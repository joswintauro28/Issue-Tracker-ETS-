import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { issuesApi } from '../api/issues';
import { usersApi } from '../api/users';
import IssueCreateForm from '../components/issues/IssueCreateForm';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import PageHeader from '../components/ui/PageHeader';
import {
  PRIORITY_BADGE_TONES,
  PRIORITY_LABELS,
  STATUS_BADGE_TONES,
  STATUS_LABELS,
  STATUS_ORDER,
  formatDate,
} from '../lib/issueFormat';
import type { Issue, IssueStatus, User } from '../types';

export default function IssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [statusFilter, setStatusFilter] = useState<IssueStatus | ''>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadIssues = useCallback((status: IssueStatus | '') => {
    setIsLoading(true);
    issuesApi
      .list(status || undefined)
      .then(setIssues)
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    loadIssues(statusFilter);
    usersApi
      .list()
      .then(setUsers)
      .catch(() => undefined); // Assignee picker is optional; ignore failures here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function handleCreateIssue(payload: Parameters<typeof issuesApi.create>[0]) {
    setIsSubmitting(true);
    try {
      await issuesApi.create(payload);
      setIsCreateFormOpen(false);
      loadIssues(statusFilter);
    } catch (createError) {
      setError(getApiErrorMessage(createError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Issues"
        description="All reported issues across the project."
        actions={
          <Button onClick={() => setIsCreateFormOpen((open) => !open)}>
            {isCreateFormOpen ? 'Close form' : 'New issue'}
          </Button>
        }
      />

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {isCreateFormOpen && (
        <Card title="Create a new issue" className="mb-6">
          <IssueCreateForm
            users={users}
            isSubmitting={isSubmitting}
            onSubmit={handleCreateIssue}
            onCancel={() => setIsCreateFormOpen(false)}
          />
        </Card>
      )}

      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="status-filter" className="text-sm font-medium text-slate-700">
          Status:
        </label>
        <select
          id="status-filter"
          className="rounded-md border-0 py-1.5 pl-3 pr-8 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as IssueStatus | '')}
        >
          <option value="">All</option>
          {STATUS_ORDER.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </div>

      <Card bodyClassName="p-0">
        {isLoading ? (
          <p className="p-5 text-sm text-slate-500">Loading issues…</p>
        ) : issues.length === 0 ? (
          <p className="p-5 text-sm text-slate-500">
            No issues found. Create the first one with “New issue”.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Title</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Priority</th>
                  <th className="px-5 py-3">Assignee</th>
                  <th className="px-5 py-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {issues.map((issue) => (
                  <tr key={issue.id} className="transition hover:bg-slate-50">
                    <td className="px-5 py-3 text-slate-500">#{issue.id}</td>
                    <td className="px-5 py-3 font-medium text-slate-900">
                      <Link to={`/issues/${issue.id}`} className="hover:text-indigo-600">
                        {issue.title}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={STATUS_BADGE_TONES[issue.status]}>
                        {STATUS_LABELS[issue.status]}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={PRIORITY_BADGE_TONES[issue.priority]}>
                        {PRIORITY_LABELS[issue.priority]}
                      </Badge>
                    </td>
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
    </div>
  );
}
