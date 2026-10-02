import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { issuesApi } from '../api/issues';
import { usersApi } from '../api/users';
import IssueComments from '../components/issues/IssueComments';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import PageHeader from '../components/ui/PageHeader';
import {
  PRIORITY_BADGE_TONES,
  PRIORITY_LABELS,
  PRIORITY_ORDER,
  STATUS_BADGE_TONES,
  STATUS_LABELS,
  STATUS_ORDER,
  formatDateTime,
} from '../lib/issueFormat';
import type { Issue, IssuePriority, IssueStatus, User } from '../types';

export default function IssueDetailsPage() {
  const { issueId } = useParams<{ issueId: string }>();
  const navigate = useNavigate();

  const [issue, setIssue] = useState<Issue | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState<IssueStatus>('open');
  const [priority, setPriority] = useState<IssuePriority>('medium');
  const [assigneeId, setAssigneeId] = useState<string>('');

  const loadIssue = useCallback(async () => {
    if (!issueId) return;
    setIsLoading(true);
    try {
      const loadedIssue = await issuesApi.get(Number(issueId));
      setIssue(loadedIssue);
      setStatus(loadedIssue.status);
      setPriority(loadedIssue.priority);
      setAssigneeId(loadedIssue.assignee_id ? String(loadedIssue.assignee_id) : '');
      setError(null);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
      setIssue(null);
    } finally {
      setIsLoading(false);
    }
  }, [issueId]);

  useEffect(() => {
    loadIssue();
    usersApi
      .list()
      .then(setUsers)
      .catch(() => undefined);
  }, [loadIssue]);

  async function handleSave() {
    if (!issue) return;
    setIsSaving(true);
    try {
      const updated = await issuesApi.update(issue.id, {
        status,
        priority,
        assignee_id: assigneeId ? Number(assigneeId) : null,
      });
      setIssue(updated);
      setError(null);
    } catch (saveError) {
      setError(getApiErrorMessage(saveError));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    if (!issue || !window.confirm(`Delete issue #${issue.id}? This cannot be undone.`)) {
      return;
    }
    setIsDeleting(true);
    try {
      await issuesApi.remove(issue.id);
      navigate('/issues');
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError));
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading issue…</p>;
  }

  if (!issue) {
    return (
      <div>
        <PageHeader title="Issue not found" />
        <p className="text-sm text-slate-500">
          {error ?? 'The requested issue does not exist.'}
        </p>
        <Link to="/issues" className="mt-4 inline-block text-sm font-semibold text-indigo-600">
          ← Back to issues
        </Link>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`#${issue.id} · ${issue.title}`}
        description={`Reported by ${issue.reporter.name} on ${formatDateTime(issue.created_at)}`}
        actions={
          <>
            <Link to="/issues">
              <Button variant="secondary">Back</Button>
            </Link>
            <Button variant="danger" onClick={handleDelete} isLoading={isDeleting}>
              Delete
            </Button>
          </>
        }
      />

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Description" className="lg:col-span-2">
          <div className="mb-4 flex flex-wrap gap-2">
            <Badge tone={STATUS_BADGE_TONES[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
            <Badge tone={PRIORITY_BADGE_TONES[issue.priority]}>
              {PRIORITY_LABELS[issue.priority]}
            </Badge>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {issue.description || 'No description provided.'}
          </p>
          <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-200 pt-4 text-sm">
            <div>
              <dt className="text-slate-500">Assignee</dt>
              <dd className="font-medium text-slate-900">{issue.assignee?.name ?? 'Unassigned'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Last updated</dt>
              <dd className="font-medium text-slate-900">{formatDateTime(issue.updated_at)}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Update issue">
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Status</label>
              <select
                className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                value={status}
                onChange={(event) => setStatus(event.target.value as IssueStatus)}
              >
                {STATUS_ORDER.map((value) => (
                  <option key={value} value={value}>
                    {STATUS_LABELS[value]}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Priority</label>
              <select
                className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                value={priority}
                onChange={(event) => setPriority(event.target.value as IssuePriority)}
              >
                {PRIORITY_ORDER.map((value) => (
                  <option key={value} value={value}>
                    {PRIORITY_LABELS[value]}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Assignee</label>
              <select
                className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                value={assigneeId}
                onChange={(event) => setAssigneeId(event.target.value)}
              >
                <option value="">Unassigned</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>

            <Button onClick={handleSave} isLoading={isSaving} className="w-full">
              Save changes
            </Button>
          </div>
        </Card>
      </div>

      <IssueComments issueId={issue.id} />
    </div>
  );
}
