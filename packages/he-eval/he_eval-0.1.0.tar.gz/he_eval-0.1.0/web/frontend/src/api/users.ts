import { api } from './client';
import type { User, UserCreate } from '../types';

export const users = {
  list: () => api.get<User[]>('/api/v1/users'),
  get: (id: string) => api.get<User>(`/api/v1/users/${id}`),
  create: (data: UserCreate) => api.post<User>('/api/v1/users', data),
  delete: (id: string) => api.delete<void>(`/api/v1/users/${id}`),
  me: () => api.get<User>('/api/v1/users/me'),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<void>('/api/v1/users/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  resetPassword: (userId: string, newPassword: string) =>
    api.post<void>(`/api/v1/users/${userId}/reset-password`, {
      new_password: newPassword,
    }),
};
