import type { DashboardSummary } from '../types';
import { apiClient } from './client';

export const dashboardApi = {
  /** Aggregated counters and lists, computed by the backend on each request. */
  summary: () =>
    apiClient.get<DashboardSummary>('/dashboard/summary').then((response) => response.data),
};
