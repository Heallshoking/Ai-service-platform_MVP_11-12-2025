import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import Icon from '@/components/ui/icon';
import { Notification } from '@/types/notification';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import ContactModal from '@/components/ContactModal';

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showContactModal, setShowContactModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = () => {
    const storedNotifications = localStorage.getItem('notifications');
    if (storedNotifications) {
      setNotifications(JSON.parse(storedNotifications));
    }
  };

  const markAsRead = (id: string) => {
    const updated = notifications.map(n => 
      n.id === id ? { ...n, read: true } : n
    );
    setNotifications(updated);
    localStorage.setItem('notifications', JSON.stringify(updated));
  };

  const markAllAsRead = () => {
    const updated = notifications.map(n => ({ ...n, read: true }));
    setNotifications(updated);
    localStorage.setItem('notifications', JSON.stringify(updated));
  };

  const clearAll = () => {
    setNotifications([]);
    localStorage.removeItem('notifications');
  };

  const handleNotificationClick = (notification: Notification) => {
    markAsRead(notification.id);
    if (notification.orderId) {
      navigate('/orders');
    }
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'order_created':
        return 'ShoppingBag';
      case 'order_status_changed':
        return 'CheckCircle';
      case 'order_assigned':
        return 'UserCheck';
      case 'payment_received':
        return 'CreditCard';
      case 'executor_on_way':
        return 'Navigation';
      case 'executor_arrived':
        return 'MapPin';
      case 'phone_access':
        return 'Phone';
      default:
        return 'Info';
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />

        <div className="bg-white shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <Icon name="Bell" size={24} />
                Уведомления
              </h1>
              {unreadCount > 0 && (
                <p className="text-sm text-gray-600 mt-1">
                  {unreadCount} {unreadCount === 1 ? 'непрочитанное' : 'непрочитанных'}
                </p>
              )}
            </div>
            {notifications.length > 0 && (
              <div className="flex gap-2">
                <Button variant="ghost" size="icon" onClick={clearAll}>
                  <Icon name="Trash2" size={16} />
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="p-6">
          {notifications.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="mb-4">
                <div className="w-20 h-20 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                  <Icon name="Bell" size={40} className="text-gray-400" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">Нет уведомлений</h3>
              <p className="text-gray-600">
                Здесь будут появляться важные сообщения о ваших заявках
              </p>
            </Card>
          ) : (
            <>
              <div className="space-y-2">
                {notifications.map((notification) => (
                  <Card
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                    notification.read
                      ? 'bg-white'
                      : (notification as any).priority === 'high'
                      ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-purple-300 border-2 shadow-lg'
                      : 'bg-blue-50 border-blue-200 border-2'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-full flex-shrink-0 ${
                      notification.read 
                        ? 'bg-gray-100' 
                        : (notification as any).priority === 'high'
                        ? 'bg-gradient-to-br from-purple-100 to-blue-100'
                        : 'bg-blue-100'
                    }`}>
                      <Icon 
                        name={getIcon(notification.type)} 
                        size={20} 
                        className={notification.read ? 'text-gray-600' : 'text-primary'} 
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className={`font-medium ${notification.read ? 'text-gray-700' : 'text-gray-900'}`}>
                          {notification.title}
                        </h4>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-1" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(notification.createdAt).toLocaleString('ru-RU')}
                      </p>
                    </div>
                  </div>
                  </Card>
                ))}
              </div>
              
              {unreadCount > 0 && (
                <div className="mt-4">
                  <Button 
                    variant="outline" 
                    className="w-full" 
                    onClick={markAllAsRead}
                  >
                    Прочитать все
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
    </div>
  );
}