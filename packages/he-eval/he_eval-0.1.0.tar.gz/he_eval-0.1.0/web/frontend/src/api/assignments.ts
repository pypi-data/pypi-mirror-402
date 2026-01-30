import { api } from './client';
import type { Assignment, AssignmentCreate } from '../types';

export interface AssignmentUpdate {
  status?: string;
  priority?: number;
  task_id?: string;
  side_task?: string;
}

export interface BulkAssignmentCreate {
  user_ids: string[];
  setting: string;
  task_id: string;
  side_task: string;
  priority?: number;
}

export const assignments = {
  list: () => api.get<Assignment[]>('/api/v1/assignments'),
  listAll: () => api.get<Assignment[]>('/api/v1/assignments?all=true'),
  get: (id: string) => api.get<Assignment>(`/api/v1/assignments/${id}`),
  create: (data: AssignmentCreate) =>
    api.post<Assignment>('/api/v1/assignments', data),
  createBulk: (data: BulkAssignmentCreate) =>
    api.post<Assignment[]>('/api/v1/assignments/bulk', data),
  update: (id: string, data: AssignmentUpdate) =>
    api.patch<Assignment>(`/api/v1/assignments/${id}`, data),
  delete: (id: string) => api.delete<void>(`/api/v1/assignments/${id}`),
};
