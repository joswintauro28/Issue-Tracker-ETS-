import type { RegisterPayload, Token, User } from '../types';
import { apiClient } from './client';

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<User>('/auth/register', payload).then((response) => response.data),

  login: (payload: { email: string; password: string }) =>
    apiClient.post<Token>('/auth/login', payload).then((response) => response.data),

  me: () => apiClient.get<User>('/auth/me').then((response) => response.data),
};
