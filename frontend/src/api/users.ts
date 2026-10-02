import type { User } from '../types';
import { apiClient } from './client';

export const usersApi = {
  list: () => apiClient.get<User[]>('/users').then((response) => response.data),
};
