import type { Issue, IssueCreatePayload, IssueStatus, IssueUpdatePayload } from '../types';
import { apiClient } from './client';

export const issuesApi = {
  list: (status?: IssueStatus) =>
    apiClient
      .get<Issue[]>('/issues', { params: status ? { status } : undefined })
      .then((response) => response.data),

  get: (issueId: number) =>
    apiClient.get<Issue>(`/issues/${issueId}`).then((response) => response.data),

  create: (payload: IssueCreatePayload) =>
    apiClient.post<Issue>('/issues', payload).then((response) => response.data),

  update: (issueId: number, payload: IssueUpdatePayload) =>
    apiClient.patch<Issue>(`/issues/${issueId}`, payload).then((response) => response.data),

  remove: (issueId: number) => apiClient.delete<void>(`/issues/${issueId}`),
};
