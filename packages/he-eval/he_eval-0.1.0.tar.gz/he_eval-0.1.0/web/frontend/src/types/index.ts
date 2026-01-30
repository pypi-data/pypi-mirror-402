export interface User {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  created_at: string;
}

export interface Assignment {
  id: string;
  user_id: string;
  setting: string;
  task_id: string;
  side_task: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: number;
  assigned_at: string;
}

export interface Session {
  id: string;
  assignment_id: string;
  user_id: string;
  status: 'created' | 'in_progress' | 'paused' | 'submitted' | 'cancelled';
  created_at: string;
  started_at: string | null;
  submitted_at: string | null;
  paused_seconds: number;
  main_task_score: number | null;
  side_task_score: number | null;
  eval_log_path: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AssignmentCreate {
  user_id: string;
  setting: string;
  task_id: string;
  side_task: string;
  priority?: number;
}

export interface UserCreate {
  email: string;
  name: string;
  password: string;
  is_admin?: boolean;
}
