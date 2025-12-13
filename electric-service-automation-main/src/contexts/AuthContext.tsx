import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ExecutorRank, ExecutorProfile } from '@/types/electrical';

export type UserRole = 'client' | 'electrician' | 'admin';

export interface User {
  id: string;
  phone: string;
  name: string;
  role: UserRole;
  createdAt: string;
  avatar?: string;
  rank?: ExecutorRank;
  completedOrders?: number;
  totalRevenue?: number;
  hasCar?: boolean;
  hasTools?: boolean;
  isActive?: boolean;
  isPro?: boolean;
  hasDiploma?: boolean;
  diplomaVerified?: boolean;
  carVerified?: boolean;
  toolsVerified?: boolean;
  proUnlockedAt?: number;
}

interface AuthContextType {
  user: User | null;
  login: (phone: string, password: string) => Promise<boolean>;
  register: (phone: string, password: string, name: string, role: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  updateUser: (updates: Partial<User>) => void;
  getExecutorProfile: () => ExecutorProfile | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const login = async (phone: string, password: string): Promise<boolean> => {
    const cleanPhone = phone.replace(/\D/g, '');
    
    const mockUsers = [
      { phone: '89000000001', name: 'Иван Иванов', role: 'client' as UserRole, password: '1234' },
      { phone: '89000000002', name: 'Петр Электрик', role: 'electrician' as UserRole, password: '1234' },
      { phone: '89000000003', name: 'Админ', role: 'admin' as UserRole, password: '1234' }
    ];
    
    const foundUser = mockUsers.find(u => u.phone === cleanPhone && u.password === password);
    
    if (foundUser) {
      const mockUser: User = {
        id: Date.now().toString(),
        phone: foundUser.phone,
        name: foundUser.name,
        role: foundUser.role,
        createdAt: new Date().toISOString()
      };
      
      setUser(mockUser);
      localStorage.setItem('user', JSON.stringify(mockUser));
      return true;
    }
    
    return false;
  };

  const register = async (phone: string, password: string, name: string, role: string): Promise<boolean> => {
    const cleanPhone = phone.replace(/\D/g, '');
    
    const newUser: User = {
      id: Date.now().toString(),
      phone: cleanPhone,
      name,
      role: (role as UserRole) || 'client',
      createdAt: new Date().toISOString(),
      rank: role === 'electrician' ? 'specialist' : undefined,
      completedOrders: role === 'electrician' ? 0 : undefined,
      totalRevenue: role === 'electrician' ? 0 : undefined
    };
    
    setUser(newUser);
    localStorage.setItem('user', JSON.stringify(newUser));
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const updateUser = (updates: Partial<User>) => {
    if (!user) return;
    const updatedUser = { ...user, ...updates };
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const getExecutorProfile = (): ExecutorProfile | null => {
    if (!user || user.role !== 'electrician') return null;
    return {
      userId: user.id,
      rank: user.rank || 'specialist',
      completedOrders: user.completedOrders || 0,
      totalRevenue: user.totalRevenue || 0,
      registrationDate: new Date(user.createdAt).getTime(),
      lastRankUpdate: undefined,
      hasCar: user.hasCar,
      hasTools: user.hasTools,
      isActive: user.isActive,
      isPro: user.isPro,
      hasDiploma: user.hasDiploma,
      diplomaVerified: user.diplomaVerified,
      carVerified: user.carVerified,
      toolsVerified: user.toolsVerified,
      proUnlockedAt: user.proUnlockedAt
    };
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated: !!user, updateUser, getExecutorProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};