import { useAuth, UserRole } from '@/contexts/AuthContext';

export interface Permissions {
  canViewAllOrders: boolean;
  canEditOrders: boolean;
  canDeleteOrders: boolean;
  canManageUsers: boolean;
  canViewAnalytics: boolean;
  canEditPrices: boolean;
  canAcceptOrders: boolean;
  canCompleteOrders: boolean;
}

const rolePermissions: Record<UserRole, Permissions> = {
  client: {
    canViewAllOrders: false,
    canEditOrders: false,
    canDeleteOrders: false,
    canManageUsers: false,
    canViewAnalytics: false,
    canEditPrices: false,
    canAcceptOrders: false,
    canCompleteOrders: false
  },
  electrician: {
    canViewAllOrders: true,
    canEditOrders: true,
    canDeleteOrders: false,
    canManageUsers: false,
    canViewAnalytics: false,
    canEditPrices: false,
    canAcceptOrders: true,
    canCompleteOrders: true
  },
  admin: {
    canViewAllOrders: true,
    canEditOrders: true,
    canDeleteOrders: true,
    canManageUsers: true,
    canViewAnalytics: true,
    canEditPrices: true,
    canAcceptOrders: true,
    canCompleteOrders: true
  }
};

export function usePermissions(): Permissions {
  const { user } = useAuth();
  
  if (!user) {
    return rolePermissions.client;
  }
  
  return rolePermissions[user.role];
}
