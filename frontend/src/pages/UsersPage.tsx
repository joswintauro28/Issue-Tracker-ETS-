import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getApiErrorMessage } from '../api/client';
import { usersApi } from '../api/users';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import PageHeader from '../components/ui/PageHeader';
import { formatDate } from '../lib/issueFormat';
import type { User, UserRole } from '../types';

const ROLE_BADGE_TONES: Record<UserRole, 'indigo' | 'gray'> = {
  admin: 'indigo',
  user: 'gray',
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAdmin } = useAuth();

  useEffect(() => {
    // The users list exists for assignment pickers; only admins may load it.
    if (!isAdmin) {
      setIsLoading(false);
      return;
    }
    usersApi
      .list()
      .then(setUsers)
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
      .finally(() => setIsLoading(false));
  }, [isAdmin]);

  if (!isAdmin) {
    return (
      <div>
        <PageHeader title="Users" description="Restricted to administrators." />
        <Card>
          <p className="text-sm text-slate-700">
            You do not have permission to view the user list. Ask an administrator if you need
            access.
          </p>
          <Link to="/" className="mt-3 inline-block text-sm font-semibold text-indigo-600">
            ← Back to dashboard
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Users"
        description="Everyone registered on this Issue Tracker instance."
      />

      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <Card bodyClassName="p-0">
        {isLoading ? (
          <p className="p-5 text-sm text-slate-500">Loading users…</p>
        ) : users.length === 0 ? (
          <p className="p-5 text-sm text-slate-500">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Email</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {users.map((user) => (
                  <tr key={user.id} className="transition hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-900">{user.name}</td>
                    <td className="px-5 py-3 text-slate-600">{user.email}</td>
                    <td className="px-5 py-3">
                      <Badge tone={ROLE_BADGE_TONES[user.role]}>{user.role}</Badge>
                    </td>
                    <td className="px-5 py-3 text-slate-500">{formatDate(user.created_at)}</td>
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
