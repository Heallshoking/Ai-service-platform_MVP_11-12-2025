import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from '@/hooks/use-toast';

interface Order {
  order_id: number;
  status: string;
  address: string;
  scheduled_date: string | null;
  scheduled_time: string | null;
  total_price: number;
  created_at: string;
  executor: {
    name: string;
    phone: string;
    rating: number;
  } | null;
  services: {
    name: string;
    quantity: number;
    price: number;
  }[];
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-500',
  assigned: 'bg-purple-500',
  in_progress: 'bg-yellow-500',
  on_way: 'bg-orange-500',
  completed: 'bg-green-500',
  cancelled: 'bg-gray-500'
};

const statusLabels: Record<string, string> = {
  new: 'Новая',
  assigned: 'Назначена',
  in_progress: 'В работе',
  on_way: 'Мастер выехал',
  completed: 'Завершена',
  cancelled: 'Отменена'
};

const Admin = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    setOrders([]);
    setLoading(false);
  };

  const updateOrderStatus = async (orderId: number, newStatus: string) => {
    try {
      const response = await fetch('https://functions.poehali.dev/9fde3ede-6010-4014-95a9-ec4e7388f476', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          status: newStatus,
          changed_by: 'admin'
        })
      });

      if (response.ok) {
        toast({
          title: "Статус обновлен",
          description: `Заказ #${orderId} → ${statusLabels[newStatus]}`
        });
        fetchOrders();
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось обновить статус",
        variant: "destructive"
      });
    }
  };

  const filteredOrders = filter === 'all' 
    ? orders 
    : orders.filter(o => o.status === filter);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon name="Shield" className="text-primary" size={24} />
              <h1 className="font-heading font-bold text-xl text-foreground">Админ-панель</h1>
            </div>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              <Icon name="ArrowLeft" size={16} className="mr-2" />
              На главную
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Заказы</h2>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все заказы</SelectItem>
              <SelectItem value="new">Новые</SelectItem>
              <SelectItem value="assigned">Назначенные</SelectItem>
              <SelectItem value="in_progress">В работе</SelectItem>
              <SelectItem value="completed">Завершенные</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <Icon name="Loader2" className="animate-spin mx-auto mb-4" size={32} />
            <p className="text-muted-foreground">Загрузка заказов...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <Card className="p-12 text-center">
            <Icon name="Package" className="mx-auto mb-4 text-muted-foreground" size={48} />
            <p className="text-muted-foreground">Заказов пока нет</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <Card key={order.order_id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-bold text-lg">Заказ #{order.order_id}</h3>
                      <Badge className={statusColors[order.status]}>
                        {statusLabels[order.status]}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {new Date(order.created_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">{order.total_price} ₽</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm font-semibold mb-1">Адрес:</p>
                    <p className="text-sm">{order.address}</p>
                  </div>
                  {order.scheduled_date && (
                    <div>
                      <p className="text-sm font-semibold mb-1">Дата и время:</p>
                      <p className="text-sm">
                        {new Date(order.scheduled_date).toLocaleDateString('ru-RU')} 
                        {order.scheduled_time && ` в ${order.scheduled_time}`}
                      </p>
                    </div>
                  )}
                </div>

                {order.executor && (
                  <div className="mb-4 p-3 bg-muted rounded-lg">
                    <p className="text-sm font-semibold mb-1">Исполнитель:</p>
                    <div className="flex items-center gap-2">
                      <Icon name="User" size={16} />
                      <span className="text-sm">{order.executor.name}</span>
                      <span className="text-sm text-muted-foreground">•</span>
                      <span className="text-sm">{order.executor.phone}</span>
                      <span className="text-sm text-muted-foreground">•</span>
                      <div className="flex items-center gap-1">
                        <Icon name="Star" size={14} className="text-yellow-500" />
                        <span className="text-sm">{order.executor.rating}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mb-4">
                  <p className="text-sm font-semibold mb-2">Услуги:</p>
                  <div className="space-y-1">
                    {order.services.map((service, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span>{service.name} x{service.quantity}</span>
                        <span className="font-semibold">{service.price * service.quantity} ₽</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Select 
                    value={order.status} 
                    onValueChange={(value) => updateOrderStatus(order.order_id, value)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new">Новая</SelectItem>
                      <SelectItem value="assigned">Назначена</SelectItem>
                      <SelectItem value="in_progress">В работе</SelectItem>
                      <SelectItem value="on_way">Мастер выехал</SelectItem>
                      <SelectItem value="completed">Завершена</SelectItem>
                      <SelectItem value="cancelled">Отменена</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
