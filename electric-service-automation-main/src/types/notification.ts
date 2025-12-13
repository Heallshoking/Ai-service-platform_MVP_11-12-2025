export type NotificationType = 'order_created' | 'order_status_changed' | 'order_assigned' | 'payment_received' | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  orderId?: string;
  read: boolean;
  createdAt: number;
}
