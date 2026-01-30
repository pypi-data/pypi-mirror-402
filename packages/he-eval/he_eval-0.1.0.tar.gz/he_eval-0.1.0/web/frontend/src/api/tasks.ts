import { api } from './client';

export interface SettingInfo {
  name: string;
  description: string;
  task_count: number;
  example_tasks: string[];
}

export interface SideTaskInfo {
  id: string;
  name: string;
  description: string;
}

export const tasks = {
  getSettings: () =>
    api.get<Record<string, SettingInfo>>('/api/v1/tasks/settings'),
  getSideTasks: (setting: string) =>
    api.get<SideTaskInfo[]>(`/api/v1/tasks/settings/${setting}/side-tasks`),
};
