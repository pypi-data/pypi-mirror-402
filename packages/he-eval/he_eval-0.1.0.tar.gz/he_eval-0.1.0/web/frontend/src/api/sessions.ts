import { api } from './client';
import type { Session } from '../types';

export const sessions = {
  create: (assignmentId: string) =>
    api.post<Session>('/api/v1/sessions', { assignment_id: assignmentId }),
  get: (id: string) => api.get<Session>(`/api/v1/sessions/${id}`),
  start: (id: string) => api.patch<Session>(`/api/v1/sessions/${id}/start`, {}),
  pause: (id: string, reason?: string) =>
    api.patch<Session>(`/api/v1/sessions/${id}/pause`, { reason }),
  resume: (id: string) =>
    api.patch<Session>(`/api/v1/sessions/${id}/resume`, {}),
  byAssignment: (assignmentId: string) =>
    api.get<Session[]>(`/api/v1/sessions/by-assignment/${assignmentId}`),
};
