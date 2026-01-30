import { createContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { auth } from '../api/auth';
import { users } from '../api/users';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('token')
  );
  const [isLoading, setIsLoading] = useState(true);

  // On mount, if we have a token, fetch the current user
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    users
      .me()
      .then(setUser)
      .catch(() => {
        // Token invalid, clear it
        localStorage.removeItem('token');
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await auth.login({ email, password });
    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);

    // Fetch user info
    const currentUser = await users.me();
    setUser(currentUser);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
