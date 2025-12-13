import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import Icon from '@/components/ui/icon';

interface Order {
  id: number;
  clientName: string;
  services: string[];
  amount: number;
  status: 'scheduled' | 'in_progress' | 'completed';
  date: string;
}

const mockOrders: Order[] = [
  {
    id: 1,
    clientName: 'Иван Петров',
    services: ['Установка розеток', 'Монтаж освещения'],
    amount: 3500,
    status: 'scheduled',
    date: '2024-11-05'
  },
  {
    id: 2,
    clientName: 'Мария Сидорова',
    services: ['Замена проводки'],
    amount: 12000,
    status: 'in_progress',
    date: '2024-11-03'
  },
  {
    id: 3,
    clientName: 'Алексей Коваль',
    services: ['Сборка щитка'],
    amount: 5500,
    status: 'completed',
    date: '2024-10-28'
  }
];

const ExecutorProfile = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('tasks');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date');

  const executor = {
    name: 'Алексей Иванов',
    rating: 4.9,
    completedOrders: 156,
    earnings: 485000,
    specializations: ['Электропроводка', 'Освещение', 'Розетки', 'Щитки']
  };

  const filteredOrders = mockOrders.filter(order => 
    statusFilter === 'all' || order.status === statusFilter
  ).sort((a, b) => {
    if (sortBy === 'amount') return b.amount - a.amount;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  const getStatusLabel = (status: string) => {
    const labels = {
      scheduled: 'Встреча назначена',
      in_progress: 'В работе',
      completed: 'Завершено'
    };
    return labels[status as keyof typeof labels];
  };

  const getStatusColor = (status: string) => {
    const colors = {
      scheduled: 'bg-blue-500',
      in_progress: 'bg-orange-500',
      completed: 'bg-green-500'
    };
    return colors[status as keyof typeof colors];
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="h-12 w-12">
                <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                  {executor.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div>
                <h1 className="font-bold text-lg">{executor.name}</h1>
                <div className="flex items-center gap-2 text-sm">
                  <Icon name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                  <span>{executor.rating}</span>
                  <span className="text-muted-foreground">• {executor.completedOrders} заказов</span>
                </div>
              </div>
            </div>
            <Button variant="ghost" size="sm">
              <Icon name="Settings" size={20} />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
            <TabsTrigger value="tasks">Задачи</TabsTrigger>
            <TabsTrigger value="specialization">Специализация</TabsTrigger>
            <TabsTrigger value="services">Услуги</TabsTrigger>
            <TabsTrigger value="rating">Рейтинг</TabsTrigger>
            <TabsTrigger value="wallet">Кошелёк</TabsTrigger>
          </TabsList>

          <TabsContent value="tasks" className="space-y-4">
            <Card className="p-4">
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">Фильтр по статусу</label>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Все задачи</SelectItem>
                      <SelectItem value="scheduled">Встреча назначена</SelectItem>
                      <SelectItem value="in_progress">В работе</SelectItem>
                      <SelectItem value="completed">Завершено</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">Сортировка</label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="date">По дате</SelectItem>
                      <SelectItem value="amount">По стоимости</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-3">
                {filteredOrders.map(order => (
                  <Card key={order.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">{order.clientName}</h3>
                        <p className="text-sm text-muted-foreground">
                          {new Date(order.date).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                      <Badge className={`${getStatusColor(order.status)} text-white`}>
                        {getStatusLabel(order.status)}
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-1">
                        {order.services.map((service, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                      
                      <div className="flex items-center justify-between pt-2">
                        <span className="font-bold text-lg text-primary">
                          {order.amount.toLocaleString()} ₽
                        </span>
                        <Button size="sm" variant="outline">
                          Подробнее
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="specialization" className="space-y-4">
            <Card className="p-6">
              <h2 className="font-bold text-xl mb-4">Моя специализация</h2>
              <p className="text-muted-foreground mb-6">
                Выберите направления, в которых вы специализируетесь
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {['Электропроводка', 'Освещение', 'Розетки', 'Щитки', 'Автоматика', 'Диагностика'].map((spec) => (
                  <Button
                    key={spec}
                    variant={executor.specializations.includes(spec) ? 'default' : 'outline'}
                    className="h-auto py-4"
                  >
                    {spec}
                  </Button>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="services" className="space-y-4">
            <Card className="p-6">
              <h2 className="font-bold text-xl mb-4">Мои услуги</h2>
              <p className="text-muted-foreground mb-6">
                Услуги, на которых вы будете показаны клиентам
              </p>
              <div className="space-y-2">
                {['Установка розеток', 'Монтаж освещения', 'Замена проводки', 'Сборка щитков'].map((service) => (
                  <div key={service} className="flex items-center justify-between p-3 border rounded-lg">
                    <span>{service}</span>
                    <Button variant="ghost" size="sm">
                      <Icon name="Check" size={18} className="text-primary" />
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="rating" className="space-y-4">
            <Card className="p-6">
              <div className="text-center space-y-4">
                <div>
                  <div className="text-6xl font-bold text-primary">{executor.rating}</div>
                  <div className="flex items-center justify-center gap-1 mt-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Icon key={star} name="Star" size={24} className="text-yellow-500 fill-yellow-500" />
                    ))}
                  </div>
                </div>
                
                <Separator />
                
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-3xl font-bold">{executor.completedOrders}</div>
                    <div className="text-sm text-muted-foreground">Завершено заказов</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold">98%</div>
                    <div className="text-sm text-muted-foreground">Положительных отзывов</div>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="wallet" className="space-y-4">
            <Card className="p-6">
              <h2 className="font-bold text-xl mb-6">Аналитика заработка</h2>
              
              <div className="space-y-4 mb-8">
                <div>
                  <label className="text-sm font-medium mb-2 block">Период</label>
                  <Select defaultValue="30">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">За 1 день</SelectItem>
                      <SelectItem value="30">За 30 дней</SelectItem>
                      <SelectItem value="year">Выбрать год</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="bg-primary/5 rounded-lg p-6 text-center">
                  <div className="text-sm text-muted-foreground mb-2">Заработано за период</div>
                  <div className="text-4xl font-bold text-primary">
                    {executor.earnings.toLocaleString()} ₽
                  </div>
                </div>
              </div>

              <Button size="lg" className="w-full gap-2">
                <Icon name="Wallet" size={20} />
                Обналичить счёт
              </Button>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="mt-6 grid md:grid-cols-2 gap-4">
          <Button variant="outline" size="lg" className="gap-2">
            <Icon name="Calendar" size={20} />
            Интеграции
          </Button>
          <Button variant="outline" size="lg" className="gap-2">
            <Icon name="MessageCircle" size={20} />
            Техподдержка
          </Button>
        </div>
      </main>
    </div>
  );
};

export default ExecutorProfile;
