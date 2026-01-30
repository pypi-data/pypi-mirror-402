import { api } from './client';
import type { LoginRequest, LoginResponse } from '../types';

export const auth = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/api/v1/auth/login', data),
};
