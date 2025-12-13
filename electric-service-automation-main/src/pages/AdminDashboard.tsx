import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeSection, setActiveSection] = useState('home');
  const [stats, setStats] = useState({
    clients: 74,
    orders: 32,
    totalRevenue: 1281490,
    avgCheck: 40046
  });

  const menuItems = [
    { id: 'home', label: 'Главная', icon: 'Home' },
    { id: 'products', label: 'Товары и услуги', icon: 'Package', link: '/admin-products' },
    { id: 'users', label: 'Пользователи', icon: 'Users', link: '/admin-users' },
    { id: 'orders', label: 'Заказы', icon: 'ShoppingCart' },
    { id: 'reviews', label: 'Отзывы', icon: 'Star' },
    { id: 'banners', label: 'Баннеры', icon: 'Image' },
    { id: 'mailings', label: 'Рассылки', icon: 'Send' },
    { id: 'settings', label: 'Настройки', icon: 'Settings' },
    { id: 'analytics', label: 'Аналитика', icon: 'BarChart3' },
    { id: 'integrations', label: 'Интеграции', icon: 'Plug' },
    { id: 'support', label: 'Техподдержка', icon: 'HelpCircle' }
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'home':
        return (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold">Главная страница</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold">{stats.clients}</p>
                    <p className="text-sm text-muted-foreground">клиентов</p>
                  </div>
                  <Icon name="Users" size={40} className="text-blue-500" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold">{stats.orders}</p>
                    <p className="text-sm text-muted-foreground">заказов</p>
                  </div>
                  <Icon name="ShoppingCart" size={40} className="text-green-500" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold">{stats.totalRevenue.toLocaleString()} ₽</p>
                    <p className="text-sm text-muted-foreground">сумма заказов</p>
                  </div>
                  <Icon name="Wallet" size={40} className="text-purple-500" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold">{stats.avgCheck.toLocaleString()} ₽</p>
                    <p className="text-sm text-muted-foreground">средний чек</p>
                  </div>
                  <Icon name="TrendingUp" size={40} className="text-orange-500" />
                </div>
              </Card>
            </div>

            <Card className="p-6 bg-gradient-to-r from-primary/10 to-primary/5">
              <div className="flex items-center gap-4">
                <Icon name="Gift" size={48} className="text-primary" />
                <div>
                  <h3 className="text-xl font-bold">Новое обновление платформы! 🎉</h3>
                  <p className="text-sm text-muted-foreground">Теперь доступна система ПРОФИ кабинетов для исполнителей</p>
                </div>
                <Button className="ml-auto">Читать подробнее</Button>
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="font-bold text-lg mb-4">QR-код вашего магазина</h3>
                <div className="bg-muted h-40 rounded-lg flex items-center justify-center mb-4">
                  <Icon name="QrCode" size={80} className="text-muted-foreground" />
                </div>
                <Button className="w-full">Скачать QR-код</Button>
              </Card>

              <Card className="p-6">
                <h3 className="font-bold text-lg mb-4">Ваш тарифный план</h3>
                <div className="bg-gradient-to-r from-yellow-100 to-yellow-200 dark:from-yellow-900 dark:to-yellow-800 p-4 rounded-lg mb-4">
                  <p className="text-2xl font-bold">Премиум</p>
                  <p className="text-sm">Все возможности платформы</p>
                </div>
                <Button className="w-full" variant="outline">Управление подпиской</Button>
              </Card>
            </div>

            <Card className="p-6">
              <h3 className="font-bold text-lg mb-4">Ваш менеджер технической поддержки</h3>
              <div className="flex items-center gap-4">
                <Icon name="MessageCircle" size={48} className="text-primary" />
                <div>
                  <p className="font-medium">t.me/webbot_shop</p>
                  <Button size="sm" className="mt-2">Написать</Button>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-bold text-lg mb-4">Подключить уведомления о заказах в Telegram</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-muted-foreground">Укажите ваш ID</label>
                  <input 
                    type="text" 
                    className="w-full mt-2 px-4 py-2 border rounded-lg"
                    placeholder="Ваш Telegram ID"
                  />
                </div>
                <p className="text-sm text-green-600">✓ Уведомления подключены</p>
                <Button>Сохранить</Button>
                <p className="text-sm text-muted-foreground">или</p>
                <Button variant="outline">Запустите нашего бота</Button>
              </div>
            </Card>
          </div>
        );
      
      case 'clients':
        return (
          <div>
            <h2 className="text-3xl font-bold mb-6">Клиенты</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Список клиентов пуст</p>
            </Card>
          </div>
        );
      
      case 'orders':
        return (
          <div>
            <h2 className="text-3xl font-bold mb-6">Заказы</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Заказов пока нет</p>
            </Card>
          </div>
        );
      
      default:
        return (
          <div>
            <h2 className="text-3xl font-bold mb-6">{menuItems.find(m => m.id === activeSection)?.label}</h2>
            <Card className="p-6">
              <p className="text-muted-foreground">Раздел в разработке</p>
            </Card>
          </div>
        );
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
              <p className="text-xs text-muted-foreground">Админ-панель</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" onClick={logout}>
              Выйти
            </Button>
            <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center text-white font-bold">
              A
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="w-64 border-r border-border bg-card h-[calc(100vh-73px)] sticky top-[73px] overflow-y-auto">
          <nav className="p-4 space-y-1">
            {menuItems.map(item => (
              <button
                key={item.id}
                onClick={() => item.link ? navigate(item.link) : setActiveSection(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
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

        <main className="flex-1 p-6 max-w-7xl mx-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;