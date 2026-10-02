import { useEffect, useState, type FormEvent } from 'react';

import { getApiErrorMessage } from '../../api/client';
import { commentsApi } from '../../api/comments';
import { useToast } from '../../context/ToastContext';
import { formatDateTime } from '../../lib/issueFormat';
import type { Comment } from '../../types';
import Button from '../ui/Button';
import Card from '../ui/Card';

export default function IssueComments({ issueId }: { issueId: number }) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    commentsApi
      .list(issueId)
      .then((loaded) => {
        if (isMounted) setComments(loaded);
      })
      .catch((loadError) => {
        if (isMounted) setError(getApiErrorMessage(loadError));
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [issueId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!content.trim()) {
      setError('Comment cannot be empty.');
      return;
    }
    setIsSubmitting(true);
    try {
      const created = await commentsApi.create(issueId, content.trim());
      setComments((previous) => [...previous, created]);
      setContent('');
      setError(null);
      showToast('Comment posted.');
    } catch (submitError) {
      setError(getApiErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card title={`Comments (${comments.length})`} className="mt-6">
      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading comments…</p>
      ) : comments.length === 0 ? (
        <p className="text-sm text-slate-500">No comments yet. Start the discussion below.</p>
      ) : (
        <ul className="mb-6 space-y-4">
          {comments.map((comment) => (
            <li key={comment.id} className="flex gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                {comment.author.name.charAt(0).toUpperCase()}
              </span>
              <div className="min-w-0 flex-1 rounded-md bg-slate-50 px-4 py-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-900">{comment.author.name}</p>
                  <p className="text-xs text-slate-500">{formatDateTime(comment.created_at)}</p>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{comment.content}</p>
              </div>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="space-y-3 border-t border-slate-200 pt-4">
        <label htmlFor="new-comment" className="block text-sm font-medium text-slate-700">
          Add a comment
        </label>
        <textarea
          id="new-comment"
          rows={3}
          className="block w-full rounded-md border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-600"
          placeholder="Write a comment…"
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
        <div className="flex justify-end">
          <Button type="submit" isLoading={isSubmitting}>
            Post comment
          </Button>
        </div>
      </form>
    </Card>
  );
}
