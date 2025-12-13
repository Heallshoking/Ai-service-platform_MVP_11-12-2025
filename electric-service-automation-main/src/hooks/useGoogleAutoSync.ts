import { useEffect } from 'react';
import { Order } from '@/types/electrical';
import { googleAuth } from '@/lib/googleAuth';
import { googleCalendar } from '@/lib/googleCalendar';
import { googleTasks } from '@/lib/googleTasks';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from './usePermissions';

export function useGoogleAutoSync(orders: Order[]) {
  const { isAuthenticated } = useAuth();
  const permissions = usePermissions();

  useEffect(() => {
    if (!isAuthenticated || !googleAuth.isAuthenticated()) {
      return;
    }

    const syncOrders = async () => {
      for (const order of orders) {
        if (permissions.isAdmin && !order.googleCalendarEventId) {
          const event = await googleCalendar.createEvent(order);
          if (event) {
            console.log(`Auto-synced order ${order.id} to Google Calendar`);
          }
        }

        if (permissions.isExecutor && order.assignedTo === 'current-executor-id' && !order.googleTaskId) {
          const task = await googleTasks.createTask(order, order.assignedToName || 'Исполнитель');
          if (task) {
            console.log(`Auto-synced order ${order.id} to Google Tasks`);
          }
        }
      }
    };

    syncOrders();
  }, [orders, isAuthenticated, permissions]);
}
