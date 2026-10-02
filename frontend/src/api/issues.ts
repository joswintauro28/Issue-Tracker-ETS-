import type {
  Issue,
  IssueCreatePayload,
  IssueEditPayload,
  IssueStatus,
  Paginated,
} from '../types';
import { apiClient } from './client';

export interface IssueListParams {
  page?: number;
  pageSize?: number;
  status?: IssueStatus | '';
  /** '' = no filter, 'unassigned' = only unassigned issues, otherwise a user id. */
  assignee?: number | 'unassigned' | '';
  search?: string;
}

function buildQuery(params: IssueListParams): Record<string, string | number | boolean> {
  const query: Record<string, string | number | boolean> = {};
  if (params.page && params.page > 1) {
    query.page = params.page;
  }
  if (params.pageSize && params.pageSize !== 10) {
    query.page_size = params.pageSize;
  }
  if (params.status) {
    query.status = params.status;
  }
  if (params.assignee === 'unassigned') {
    query.unassigned = true;
  } else if (params.assignee !== '') {
    const assigneeId = Number(params.assignee);
    if (!Number.isNaN(assigneeId)) {
      query.assignee_id = assigneeId;
    }
  }
  if (params.search && params.search.trim()) {
    query.search = params.search.trim();
  }
  return query;
}

export const issuesApi = {
  list: (params: IssueListParams = {}) =>
    apiClient.get<Paginated<Issue>>('/issues', { params: buildQuery(params) }).then((r) => r.data),

  get: (issueId: number) =>
    apiClient.get<Issue>(`/issues/${issueId}`).then((response) => response.data),

  create: (payload: IssueCreatePayload) =>
    apiClient.post<Issue>('/issues', payload).then((response) => response.data),

  edit: (issueId: number, payload: IssueEditPayload) =>
    apiClient.put<Issue>(`/issues/${issueId}`, payload).then((response) => response.data),

  updateStatus: (issueId: number, status: IssueStatus) =>
    apiClient
      .patch<Issue>(`/issues/${issueId}/status`, { status })
      .then((response) => response.data),

  assign: (issueId: number, assigneeId: number | null) =>
    apiClient
      .patch<Issue>(`/issues/${issueId}/assign`, { assignee_id: assigneeId })
      .then((response) => response.data),

  remove: (issueId: number) => apiClient.delete<void>(`/issues/${issueId}`),
};
