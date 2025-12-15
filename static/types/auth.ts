export type UserRole = 'client' | 'electrician' | 'admin';

export interface User {
  id: string;
  phone: string;
  name: string;
  role: UserRole;
  createdAt: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}
