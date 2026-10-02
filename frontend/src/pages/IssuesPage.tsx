import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { issuesApi } from '../api/issues';
import { usersApi } from '../api/users';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import IssueForm from '../components/issues/IssueForm';
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
import type { Issue, IssueFormValues, IssueStatus, Paginated, User } from '../types';

const PAGE_SIZE = 10;

/** '' = all, 'unassigned', or a user id as a string. */
type AssigneeFilter = string;

function toAssigneeParam(value: AssigneeFilter): number | 'unassigned' | '' {
  if (value === '' || value === 'unassigned') {
    return value;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? '' : parsed;
}

export default function IssuesPage() {
  const [data, setData] = useState<Paginated<Issue> | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  const [statusFilter, setStatusFilter] = useState<IssueStatus | ''>('');
  const [assigneeFilter, setAssigneeFilter] = useState<AssigneeFilter>('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();
  const { isAdmin } = useAuth();

  // Debounce the search box so typing does not spam the API.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const loadIssues = useCallback(() => {
    setIsLoading(true);
    issuesApi
      .list({
        page,
        pageSize: PAGE_SIZE,
        status: statusFilter,
        assignee: toAssigneeParam(assigneeFilter),
        search,
      })
      .then((result) => {
        setData(result);
        setError(null);
        // If the current page no longer exists (data shrank), fall back to page 1.
        if (result.items.length === 0 && result.total > 0 && page > 1) {
          setPage(1);
        }
      })
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
      .finally(() => setIsLoading(false));
  }, [page, statusFilter, assigneeFilter, search]);

  useEffect(() => {
    loadIssues();
  }, [loadIssues]);

  useEffect(() => {
    if (isAdmin) {
      usersApi
        .list()
        .then(setUsers)
        .catch(() => undefined); // The assignee picker is optional; ignore load failures.
    }
  }, [isAdmin]);

  function changeStatusFilter(value: IssueStatus | '') {
    setStatusFilter(value);
    setPage(1);
  }

  function changeAssigneeFilter(value: AssigneeFilter) {
    setAssigneeFilter(value);
    setPage(1);
  }

  async function handleCreateIssue(values: IssueFormValues) {
    setIsSubmitting(true);
    try {
      const created = await issuesApi.create(values);
      setIsFormOpen(false);
      setError(null);
      showToast(`Issue #${created.id} created.`);
      // Issues are sorted newest first, so jump back to page 1 to see it.
      if (page === 1) {
        loadIssues();
      } else {
        setPage(1);
      }
    } catch (createError) {
      setError(getApiErrorMessage(createError));
    } finally {
      setIsSubmitting(false);
    }
  }

  const issues = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const hasActiveFilters = Boolean(statusFilter || assigneeFilter || search);

  const subtitle = isAdmin
    ? `${total} issue${total === 1 ? '' : 's'} across the project.`
    : `${total} task${total === 1 ? '' : 's'} assigned to you.`;

  return (
    <div>
      <PageHeader
        title={isAdmin ? 'Issues' : 'My tasks'}
        description={subtitle}
        actions={
          isAdmin ? (
            <Button onClick={() => setIsFormOpen((open) => !open)}>
              {isFormOpen ? 'Close form' : 'New issue'}
            </Button>
          ) : undefined
        }
      />

      {error && (
        <div
          className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          <span>{error}</span>
          <Button variant="secondary" size="sm" onClick={loadIssues}>
            Retry
          </Button>
        </div>
      )}

      {isFormOpen && (
        <Card title="Create a new issue" className="mb-6">
          <IssueForm
            users={users}
            isSubmitting={isSubmitting}
            submitLabel="Create issue"
            onSubmit={handleCreateIssue}
            onCancel={() => setIsFormOpen(false)}
          />
        </Card>
      )}

      <Card className="mb-4" bodyClassName="p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label htmlFor="status-filter" className="mb-1 block text-xs font-medium text-slate-500">
              Status
            </label>
            <select
              id="status-filter"
              className="block w-full rounded-md border-0 py-2 pl-3 pr-8 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
              value={statusFilter}
              onChange={(event) => changeStatusFilter(event.target.value as IssueStatus | '')}
            >
              <option value="">All statuses</option>
              {STATUS_ORDER.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </div>

          {isAdmin && (
            <div>
              <label
                htmlFor="assignee-filter"
                className="mb-1 block text-xs font-medium text-slate-500"
              >
                Assignee
              </label>
              <select
                id="assignee-filter"
                className="block w-full rounded-md border-0 py-2 pl-3 pr-8 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                value={assigneeFilter}
                onChange={(event) => changeAssigneeFilter(event.target.value)}
              >
                <option value="">Anyone</option>
                <option value="unassigned">Unassigned</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="sm:col-span-2">
            <label htmlFor="issue-search" className="mb-1 block text-xs font-medium text-slate-500">
              Search
            </label>
            <input
              id="issue-search"
              type="search"
              placeholder="Search by title or description…"
              className="block w-full rounded-md border-0 py-2 pl-3 pr-3 text-sm shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
          </div>
        </div>
      </Card>

      <Card bodyClassName="p-0">
        {isLoading ? (
          <div className="flex items-center gap-2 p-5 text-sm text-slate-500">
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
              aria-hidden="true"
            />
            Loading issues…
          </div>
        ) : issues.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-sm font-medium text-slate-900">
              {hasActiveFilters
                ? 'No issues match your filters.'
                : isAdmin
                  ? 'No issues yet.'
                  : 'No tasks assigned to you.'}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {hasActiveFilters
                ? 'Try adjusting the status, assignee or search term.'
                : isAdmin
                  ? 'Create the first one with the “New issue” button.'
                  : 'Tasks assigned to you by an admin will appear here.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Title</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Priority</th>
                  <th className="px-5 py-3">Reporter</th>
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

      {data && !isLoading && issues.length > 0 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Page {data.page} of {totalPages} · {total} issue{total === 1 ? '' : 's'}
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1 || isLoading}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages || isLoading}
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
