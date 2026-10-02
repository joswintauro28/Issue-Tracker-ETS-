import { useState, type FormEvent } from 'react';

import type { IssueFormValues, IssuePriority, User } from '../../types';
import { PRIORITY_LABELS, PRIORITY_ORDER } from '../../lib/issueFormat';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface IssueFormProps {
  users: User[];
  initialValues?: Partial<IssueFormValues>;
  isSubmitting?: boolean;
  submitLabel?: string;
  onSubmit: (values: IssueFormValues) => Promise<void>;
  onCancel?: () => void;
}

/**
 * Reusable form for creating and editing issues.
 * Used on the Issues page (create) and the Issue Details page (edit).
 */
export default function IssueForm({
  users,
  initialValues,
  isSubmitting = false,
  submitLabel = 'Save issue',
  onSubmit,
  onCancel,
}: IssueFormProps) {
  const [title, setTitle] = useState(initialValues?.title ?? '');
  const [description, setDescription] = useState(initialValues?.description ?? '');
  const [priority, setPriority] = useState<IssuePriority>(initialValues?.priority ?? 'medium');
  const [assigneeId, setAssigneeId] = useState<string>(
    initialValues?.assignee_id ? String(initialValues.assignee_id) : '',
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (title.trim().length < 3) {
      setValidationError('Title must be at least 3 characters.');
      return;
    }
    setValidationError(null);

    await onSubmit({
      title: title.trim(),
      description: description.trim(),
      priority,
      assignee_id: assigneeId ? Number(assigneeId) : null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label="Title"
            placeholder="Short summary of the issue"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            error={validationError ?? undefined}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
          <textarea
            rows={3}
            className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
            placeholder="Optional details, steps to reproduce, etc."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
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
      </div>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
