import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { issuesApi } from '../api/issues';
import { usersApi } from '../api/users';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import IssueComments from '../components/issues/IssueComments';
import IssueForm from '../components/issues/IssueForm';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import PageHeader from '../components/ui/PageHeader';
import {
  PRIORITY_BADGE_TONES,
  PRIORITY_LABELS,
  STATUS_BADGE_TONES,
  STATUS_LABELS,
  STATUS_ORDER,
  formatDateTime,
} from '../lib/issueFormat';
import type { Issue, IssueFormValues, IssueStatus, User } from '../types';

export default function IssueDetailsPage() {
  const { issueId } = useParams<{ issueId: string }>();
  const navigate = useNavigate();

  const [issue, setIssue] = useState<Issue | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [isStatusUpdating, setIsStatusUpdating] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { showToast } = useToast();
  const { isAdmin } = useAuth();

  const loadIssue = useCallback(async () => {
    if (!issueId) return;
    setIsLoading(true);
    try {
      const loaded = await issuesApi.get(Number(issueId));
      setIssue(loaded);
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
    if (isAdmin) {
      usersApi
        .list()
        .then(setUsers)
        .catch(() => undefined);
    }
  }, [loadIssue, isAdmin]);

  async function handleEditSubmit(values: IssueFormValues) {
    if (!issue) return;
    setIsSavingEdit(true);
    try {
      const updated = await issuesApi.edit(issue.id, values);
      setIssue(updated);
      setIsEditing(false);
      setError(null);
      showToast('Issue updated.');
    } catch (editError) {
      setError(getApiErrorMessage(editError));
    } finally {
      setIsSavingEdit(false);
    }
  }

  async function handleStatusChange(nextStatus: IssueStatus) {
    if (!issue || nextStatus === issue.status) return;
    setIsStatusUpdating(true);
    try {
      const updated = await issuesApi.updateStatus(issue.id, nextStatus);
      setIssue(updated);
      setError(null);
      showToast(`Status updated to ${STATUS_LABELS[updated.status]}.`);
    } catch (statusError) {
      setError(getApiErrorMessage(statusError));
    } finally {
      setIsStatusUpdating(false);
    }
  }

  async function handleAssignChange(assigneeId: string) {
    if (!issue) return;
    setIsAssigning(true);
    try {
      const updated = await issuesApi.assign(issue.id, assigneeId ? Number(assigneeId) : null);
      setIssue(updated);
      setError(null);
      showToast(updated.assignee ? `Assigned to ${updated.assignee.name}.` : 'Issue unassigned.');
    } catch (assignError) {
      setError(getApiErrorMessage(assignError));
    } finally {
      setIsAssigning(false);
    }
  }

  async function handleDelete() {
    if (!issue) return;
    setIsDeleting(true);
    try {
      await issuesApi.remove(issue.id);
      showToast(`Issue #${issue.id} deleted.`);
      navigate('/issues');
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError));
      setIsDeleting(false);
      setIsDeleteDialogOpen(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
          aria-hidden="true"
        />
        Loading issue…
      </div>
    );
  }

  if (!issue) {
    return (
      <div>
        <PageHeader title="Issue not found" />
        <p className="text-sm text-slate-500">{error ?? 'The requested issue does not exist.'}</p>
        <Link to="/issues" className="mt-4 inline-block text-sm font-semibold text-indigo-600">
          ← Back to issues
        </Link>
      </div>
    );
  }

  const currentAssigneeId = issue.assignee_id ? String(issue.assignee_id) : '';

  return (
    <div>
      <PageHeader
        title={`#${issue.id} · ${issue.title}`}
        description={`Reported by ${issue.reporter.name}`}
        actions={
          isAdmin ? (
            <>
              <Button variant="secondary" onClick={() => setIsEditing((open) => !open)}>
                {isEditing ? 'Close editor' : 'Edit'}
              </Button>
              <Button variant="danger" onClick={() => setIsDeleteDialogOpen(true)}>
                Delete
              </Button>
            </>
          ) : undefined
        }
      />

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {isEditing && (
        <Card title="Edit issue" className="mb-6">
          <IssueForm
            users={users}
            initialValues={{
              title: issue.title,
              description: issue.description,
              priority: issue.priority,
              assignee_id: issue.assignee_id,
            }}
            isSubmitting={isSavingEdit}
            submitLabel="Save changes"
            onSubmit={handleEditSubmit}
            onCancel={() => setIsEditing(false)}
          />
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Description" className="lg:col-span-2">
          <div className="mb-4 flex flex-wrap gap-2">
            <Badge tone={STATUS_BADGE_TONES[issue.status]}>{STATUS_LABELS[issue.status]}</Badge>
            <Badge tone={PRIORITY_BADGE_TONES[issue.priority]}>
              {PRIORITY_LABELS[issue.priority]}
            </Badge>
          </div>
          <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">
            {issue.description || 'No description provided.'}
          </p>
          <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-200 pt-4 text-sm">
            <div>
              <dt className="text-slate-500">Reporter</dt>
              <dd className="font-medium text-slate-900">{issue.reporter.name}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Assignee</dt>
              <dd className="font-medium text-slate-900">{issue.assignee?.name ?? 'Unassigned'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Created</dt>
              <dd className="font-medium text-slate-900">{formatDateTime(issue.created_at)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Last updated</dt>
              <dd className="font-medium text-slate-900">{formatDateTime(issue.updated_at)}</dd>
            </div>
          </dl>
        </Card>

        <Card title={isAdmin ? 'Manage issue' : 'Update status'}>
          <div className="space-y-4">
            <div>
              <label htmlFor="issue-status" className="mb-1 block text-sm font-medium text-slate-700">
                Status
              </label>
              <select
                id="issue-status"
                className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600 disabled:opacity-50"
                value={issue.status}
                disabled={isStatusUpdating}
                onChange={(event) => handleStatusChange(event.target.value as IssueStatus)}
              >
                {STATUS_ORDER.map((value) => (
                  <option key={value} value={value}>
                    {STATUS_LABELS[value]}
                  </option>
                ))}
              </select>
              {isStatusUpdating && <p className="mt-1 text-xs text-slate-400">Updating status…</p>}
            </div>

            <div>
              <label
                htmlFor="issue-assignee"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                Assignee
              </label>
              {isAdmin ? (
                <select
                  id="issue-assignee"
                  className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600 disabled:opacity-50"
                  value={currentAssigneeId}
                  disabled={isAssigning}
                  onChange={(event) => handleAssignChange(event.target.value)}
                >
                  <option value="">Unassigned</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
                  {issue.assignee?.name ?? 'Unassigned'}
                </p>
              )}
              {isAssigning && <p className="mt-1 text-xs text-slate-400">Updating assignee…</p>}
            </div>

            <p className="text-xs text-slate-400">
              {isAdmin
                ? 'Admins can create, edit, delete and assign any issue.'
                : 'You can update the status of tasks assigned to you and add comments.'}
            </p>
          </div>
        </Card>
      </div>

      <IssueComments issueId={issue.id} />

      {isDeleteDialogOpen && (
        <ConfirmDialog
          title={`Delete issue #${issue.id}?`}
          message={`"${issue.title}" and all of its comments will be permanently removed. This action cannot be undone.`}
          confirmLabel="Delete issue"
          isBusy={isDeleting}
          onConfirm={handleDelete}
          onCancel={() => setIsDeleteDialogOpen(false)}
        />
      )}
    </div>
  );
}
