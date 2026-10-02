import type { Comment } from '../types';
import { apiClient } from './client';

export const commentsApi = {
  list: (issueId: number) =>
    apiClient.get<Comment[]>(`/issues/${issueId}/comments`).then((response) => response.data),

  create: (issueId: number, content: string) =>
    apiClient
      .post<Comment>(`/issues/${issueId}/comments`, { content })
      .then((response) => response.data),
};
