import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

const ExecutorDashboard = () => {
  const { user, logout } = useAuth();
  const [activeSection, setActiveSection] = useState('tasks');

  const menuItems = [
    { id: 'tasks', label: 'Мои задачи', icon: 'ListTodo' },
    { id: 'ads', label: 'Мои объявления', icon: 'Megaphone' },
    { id: 'messages', label: 'Сообщения', icon: 'MessageSquare' },
    { id: 'orders', label: 'Заказы', icon: 'ShoppingBag' },
    { id: 'proposals', label: 'Запросы предложений', icon: 'FileText' },
    { id: 'materials', label: 'Настройки доставки', icon: 'Truck' },
    { id: 'chat', label: 'Общение с клиентами', icon: 'MessageCircle' },
    { id: 'analytics', label: 'Аналитика', icon: 'BarChart3' },
    { id: 'promotion', label: 'Продвижение', icon: 'TrendingUp' },
    { id: 'finance', label: 'Финансы и отчёты', icon: 'Wallet' },
    { id: 'settings', label: 'Профиль и настройки', icon: 'Settings' }
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'tasks':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Мои задачи</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">У вас пока нет активных задач</p>
            </Card>
          </div>
        );
      
      case 'ads':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Мои объявления</h2>
            <Button className="mb-4">
              <Icon name="Plus" size={18} className="mr-2" />
              Создать объявление
            </Button>
            <Card className="p-6">
              <p className="text-muted-foreground">Объявлений пока нет</p>
            </Card>
          </div>
        );
      
      case 'messages':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Сообщения</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Нет новых сообщений</p>
            </Card>
          </div>
        );
      
      case 'orders':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Заказы</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">История заказов пуста</p>
            </Card>
          </div>
        );
      
      case 'proposals':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Запросы предложений</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Здесь отображаются задачи, которые администратор предложил вам выполнить
            </p>
            <Card className="p-6">
              <p className="text-muted-foreground">Нет новых предложений</p>
            </Card>
          </div>
        );
      
      case 'materials':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Настройки доставки материалов</h2>
            <Card className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Настройте доставку материалов из интернет-магазина ВКонтакте
              </p>
              <Button>Настроить доставку</Button>
            </Card>
          </div>
        );
      
      case 'chat':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Общение с клиентами</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Нет активных чатов</p>
            </Card>
          </div>
        );
      
      case 'analytics':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Аналитика</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <Card className="p-6">
                <p className="text-sm text-muted-foreground">Доход за день</p>
                <p className="text-3xl font-bold">0 ₽</p>
              </Card>
              <Card className="p-6">
                <p className="text-sm text-muted-foreground">Доход за месяц</p>
                <p className="text-3xl font-bold">0 ₽</p>
              </Card>
              <Card className="p-6">
                <p className="text-sm text-muted-foreground">Доход за год</p>
                <p className="text-3xl font-bold">0 ₽</p>
              </Card>
            </div>
            <Card className="p-6">
              <h3 className="font-semibold mb-2">История заказов</h3>
              <p className="text-muted-foreground">Заказов пока нет</p>
            </Card>
          </div>
        );
      
      case 'promotion':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Продвижение</h2>
            <Card className="p-6">
              <h3 className="font-semibold mb-2">Публикация на Avito</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Публикуйте свои объявления в официальном аккаунте на Avito
              </p>
              <Button>Опубликовать объявление</Button>
            </Card>
          </div>
        );
      
      case 'finance':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Финансы и отчёты</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Финансовых операций пока нет</p>
            </Card>
          </div>
        );
      
      case 'settings':
        return (
          <div>
            <h2 className="text-2xl font-bold mb-4">Профиль и настройки</h2>
            <Card className="p-6 space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Имя</p>
                <p className="font-medium">{user?.name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Телефон</p>
                <p className="font-medium">{user?.phone}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Роль</p>
                <p className="font-medium capitalize">{user?.role}</p>
              </div>
              <Button variant="destructive" onClick={logout}>
                Выйти
              </Button>
            </Card>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon name="Zap" size={32} className="text-primary" />
            <div>
              <h1 className="text-xl font-bold">БАЛТСЕТЬ</h1>
              <p className="text-xs text-muted-foreground">ПРОФИ кабинет</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm">{user?.name}</span>
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
              {user?.name?.charAt(0) || 'П'}
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="w-64 border-r border-border bg-card h-[calc(100vh-73px)] sticky top-[73px] overflow-y-auto">
          <nav className="p-4 space-y-2">
            {menuItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === item.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                <Icon name={item.icon as any} size={20} />
                <span className="text-sm font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default ExecutorDashboard;
