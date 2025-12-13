import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';

interface HistoryOrder {
  id: number;
  date: string;
  services: string[];
  executor: string;
  amount: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
}

const mockHistory: HistoryOrder[] = [
  {
    id: 1001,
    date: '2024-10-15',
    services: ['Установка розеток', 'Монтаж светильника'],
    executor: 'Алексей Иванов',
    amount: 3200,
    status: 'completed'
  },
  {
    id: 1002,
    date: '2024-09-28',
    services: ['Замена проводки'],
    executor: 'Дмитрий Петров',
    amount: 12500,
    status: 'completed'
  },
  {
    id: 1003,
    date: '2024-09-10',
    services: ['Сборка щитка'],
    executor: 'Алексей Иванов',
    amount: 5500,
    status: 'completed'
  }
];

const OrderHistory = () => {
  const navigate = useNavigate();

  const getStatusLabel = (status: string) => {
    const labels = {
      scheduled: 'Запланирован',
      in_progress: 'В работе',
      completed: 'Завершён',
      cancelled: 'Отменён'
    };
    return labels[status as keyof typeof labels];
  };

  const getStatusColor = (status: string) => {
    const colors = {
      scheduled: 'bg-blue-500',
      in_progress: 'bg-orange-500',
      completed: 'bg-green-500',
      cancelled: 'bg-gray-500'
    };
    return colors[status as keyof typeof colors];
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <Button variant="ghost" onClick={() => navigate('/tasks')} className="gap-2">
              <Icon name="ArrowLeft" size={20} />
              Назад
            </Button>
            <h1 className="font-heading font-bold text-lg">История заявок</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {mockHistory.length === 0 ? (
            <Card className="p-12 text-center">
              <Icon name="FileText" size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="font-semibold text-lg mb-2">История пуста</h3>
              <p className="text-muted-foreground mb-6">
                У вас пока нет завершённых заказов
              </p>
              <Button onClick={() => navigate('/')}>
                Создать заявку
              </Button>
            </Card>
          ) : (
            mockHistory.map(order => (
              <Card key={order.id} className="p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="font-bold text-lg">Заявка №{order.id}</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(order.date).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                      })}
                    </div>
                  </div>
                  <Badge className={`${getStatusColor(order.status)} text-white`}>
                    {getStatusLabel(order.status)}
                  </Badge>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">Услуги:</div>
                    <div className="flex flex-wrap gap-1">
                      {order.services.map((service, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {service}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-sm">
                    <Icon name="User" size={16} className="text-muted-foreground" />
                    <span className="text-muted-foreground">Мастер:</span>
                    <span className="font-medium">{order.executor}</span>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t">
                    <span className="font-bold text-xl text-primary">
                      {order.amount.toLocaleString()} ₽
                    </span>
                    <Button variant="outline" size="sm">
                      <Icon name="Eye" size={16} className="mr-2" />
                      Подробнее
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </main>
    </div>
  );
};

export default OrderHistory;