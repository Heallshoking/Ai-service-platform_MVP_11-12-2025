import { useState, useMemo, useRef, memo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { Order, ElectricalItem } from '@/types/electrical';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import ContactModal from '@/components/ContactModal';
import OrderDetailModal from '@/components/orders/OrderDetailModal';
import RoleGate from '@/components/auth/RoleGate';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import { useGoogleAutoSync } from '@/hooks/useGoogleAutoSync';

const STATUS_LABELS = {
  'pending': 'Поиск мастера',
  'confirmed': 'Подтверждена',
  'on-the-way': 'В пути',
  'arrived': 'Прибыл',
  'in-progress': 'В работе',
  'completed': 'Завершена'
};

const STATUS_COLORS = {
  'pending': 'bg-yellow-100 text-yellow-800',
  'confirmed': 'bg-blue-100 text-blue-800',
  'on-the-way': 'bg-purple-100 text-purple-800',
  'arrived': 'bg-indigo-100 text-indigo-800',
  'in-progress': 'bg-orange-100 text-orange-800',
  'completed': 'bg-green-100 text-green-800'
};

const getServiceTypeLabel = (items: ElectricalItem[]) => {
  const hasInstallation = items.some(item => 
    item.category === 'установка' || 
    item.category === 'монтаж розеток и выключателей'
  );
  const hasWiring = items.some(item => item.category === 'проводка и кабели');
  const hasLighting = items.some(item => item.category === 'освещение');
  
  if (hasInstallation && hasWiring) return 'Комплексная установка';
  if (hasInstallation) return 'Установка оборудования';
  if (hasWiring) return 'Прокладка кабелей';
  if (hasLighting) return 'Освещение';
  return 'Электромонтаж';
};

const pluralize = (count: number, one: string, few: string, many: string): string => {
  const mod10 = count % 10;
  const mod100 = count % 100;
  
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
};

const AllOrderCard = memo(({ order, onViewDetails, updateOrderStatus }: { order: Order; onViewDetails: (order: Order) => void; updateOrderStatus: (orderId: string, status: Order['status']) => void }) => {
  return (
    <Card 
      className="p-6 hover:shadow-xl transition-all duration-300 cursor-pointer border-l-4 border-l-primary shadow-md"
      onClick={() => onViewDetails(order)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="mb-2">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-2">
              <Icon name="MapPin" size={18} className="text-primary" />
              {order.address || 'Адрес не указан'}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_COLORS[order.status]}`}>
                {STATUS_LABELS[order.status]}
              </span>
              <span className="text-xs text-gray-500">#{order.id.slice(-6)}</span>
            </div>
          </div>
          <div className="flex items-center gap-1 text-sm text-gray-500">
            <Icon name="Clock" size={14} />
            <span>
              {new Date(order.createdAt).toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
          {order.assignedToName && (
            <div className="flex items-center gap-2 mt-3 text-xs text-green-700 bg-green-50 px-3 py-1.5 rounded-lg w-fit">
              <Icon name="User" size={14} />
              <span className="font-medium">Исполнитель: {order.assignedToName}</span>
            </div>
          )}
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            {(order.totalAmount || 0).toLocaleString()} ₽
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {order.items?.length || 0} {pluralize(order.items?.length || 0, 'услуга', 'услуги', 'услуг')}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <Icon name="Phone" size={16} className="text-primary" />
          <span className="text-gray-700 font-medium">{order.phone}</span>
        </div>
        <div className="flex items-center gap-2">
          <Icon name="MapPin" size={16} className="text-primary" />
          <span className="text-gray-700">{order.address || 'Не указан'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Icon name="Zap" size={16} className="text-primary" />
          <span className="text-gray-700">{order.totalPoints} точек</span>
        </div>
        <div className="flex items-center gap-2">
          <Icon name="Cable" size={16} className="text-primary" />
          <span className="text-gray-700">~{order.estimatedCable}м кабеля</span>
        </div>
      </div>


    </Card>
  );
});

AllOrderCard.displayName = 'AllOrderCard';

type ElectricianFilter = 'new' | 'responded' | 'invited' | 'all';

export default function AllOrders() {
  const navigate = useNavigate();
  const { orders, updateOrderStatus, assignExecutor, addToCart, clearCart, markOrderAsViewed } = useCart();
  const { isAuthenticated, user } = useAuth();
  const permissions = usePermissions();
  const [showContactModal, setShowContactModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<ElectricianFilter | Order['status'] | 'all'>('all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const parentRef = useRef<HTMLDivElement>(null);

  const unviewedNewCount = useMemo(() => {
    if (!user) return 0;
    return orders.filter(order => 
      order.status === 'pending' && 
      !order.assignedTo && 
      !order.assignedExecutors?.some(ex => ex.id === user.id) &&
      !order.viewedBy?.includes(user.id)
    ).length;
  }, [orders, user]);

  useEffect(() => {
    if (filterStatus === 'new' && user) {
      const newOrders = orders.filter(o => 
        o.status === 'pending' && 
        !o.assignedTo && 
        !o.assignedExecutors?.some(ex => ex.id === user.id)
      );
      newOrders.forEach(order => {
        if (!order.viewedBy?.includes(user.id)) {
          markOrderAsViewed(order.id, user.id);
        }
      });
    }
  }, [filterStatus, orders, user, markOrderAsViewed]);
  
  const filteredOrders = useMemo(() => {
    let filtered = orders;
    
    if (!permissions.isAdmin && user) {
      if (filterStatus === 'new') {
        filtered = orders.filter(order => 
          order.status === 'pending' && !order.assignedTo && !order.assignedExecutors?.some(ex => ex.id === user.id)
        );
      } else if (filterStatus === 'responded') {
        filtered = orders.filter(order => 
          order.assignedExecutors?.some(ex => ex.id === user.id) && order.status !== 'completed'
        );
      } else if (filterStatus === 'invited') {
        filtered = orders.filter(order => 
          order.assignedTo === user.id
        );
      } else if (filterStatus !== 'all') {
        filtered = orders.filter(order => order.status === filterStatus);
      }
    } else {
      if (filterStatus !== 'all' && ['pending', 'confirmed', 'in-progress', 'completed'].includes(filterStatus)) {
        filtered = filtered.filter(order => order.status === filterStatus);
      }
    }
    
    return filtered.sort((a, b) => {
      const dateA = a.scheduledDate ? new Date(a.scheduledDate).getTime() : a.createdAt;
      const dateB = b.scheduledDate ? new Date(b.scheduledDate).getTime() : b.createdAt;
      return dateA - dateB;
    });
  }, [orders, filterStatus, permissions.isAdmin, user]);

  const rowVirtualizer = useVirtualizer({
    count: filteredOrders.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 240,
    overscan: 3,
  });
  
  useGoogleAutoSync(orders);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-6">
        <Card className="p-8 text-center">
          <Icon name="Lock" size={48} className="mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">Доступ ограничен</h2>
          <p className="text-gray-600 mb-4">Для просмотра всех заказов необходимо войти в систему</p>
          <Button onClick={() => navigate('/')}>На главную</Button>
        </Card>
      </div>
    );
  }

  return (
    <RoleGate 
      allowedRoles={['electrician', 'admin']}
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-6">
          <Card className="p-8 text-center">
            <Icon name="ShieldAlert" size={48} className="mx-auto mb-4 text-red-400" />
            <h2 className="text-2xl font-bold mb-2">Недостаточно прав</h2>
            <p className="text-gray-600 mb-4">Эта страница доступна только электрикам и администраторам</p>
            <Button onClick={() => navigate('/')}>На главную</Button>
          </Card>
        </div>
      }
    >
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
        <PageHeader />

        <div className="max-w-4xl mx-auto">
          <PageNavigation onContactClick={() => setShowContactModal(true)} />

          <div className="p-6 space-y-6">
            <div className="bg-white shadow-lg p-6 rounded-lg">
              <h1 className="text-2xl font-bold text-gray-800 mb-4">
                Поиск заказов
              </h1>

            {permissions.isAdmin ? (
              <Tabs value={filterStatus} onValueChange={(v) => setFilterStatus(v as Order['status'] | 'all')} className="w-full">
                <TabsList className="w-full grid grid-cols-5 h-auto p-1">
                  <TabsTrigger value="all" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.length}</span>
                    <span className="text-xs">Все</span>
                  </TabsTrigger>
                  <TabsTrigger value="pending" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.status === 'pending').length}</span>
                    <span className="text-xs">Новые</span>
                  </TabsTrigger>
                  <TabsTrigger value="confirmed" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.status === 'confirmed').length}</span>
                    <span className="text-xs">Принято</span>
                  </TabsTrigger>
                  <TabsTrigger value="in-progress" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.status === 'in-progress').length}</span>
                    <span className="text-xs">В работе</span>
                  </TabsTrigger>
                  <TabsTrigger value="completed" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.status === 'completed').length}</span>
                    <span className="text-xs">Готово</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            ) : (
              <Tabs value={filterStatus} onValueChange={(v) => setFilterStatus(v as ElectricianFilter)} className="w-full">
                <TabsList className="w-full grid grid-cols-3 h-auto p-1">
                  <TabsTrigger value="new" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md relative">
                    <span className="text-lg font-bold">{orders.filter(o => o.status === 'pending' && !o.assignedTo && !o.assignedExecutors?.some(ex => ex.id === user?.id)).length}</span>
                    <span className="text-xs">Новые</span>
                    {unviewedNewCount > 0 && (
                      <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold shadow-lg animate-pulse">
                        {unviewedNewCount}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="responded" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.assignedExecutors?.some(ex => ex.id === user?.id) && o.status !== 'completed').length}</span>
                    <span className="text-xs">Вы откликнулись</span>
                  </TabsTrigger>
                  <TabsTrigger value="invited" className="flex-col py-2 px-1 data-[state=active]:bg-white data-[state=active]:shadow-md">
                    <span className="text-lg font-bold">{orders.filter(o => o.assignedTo === user?.id).length}</span>
                    <span className="text-xs">Вас пригласили</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            )}
            </div>

            {filteredOrders.length === 0 ? (
              <Card className="p-12 text-center shadow-md">
                <div className="mb-4">
                  <div className="w-20 h-20 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
                    <Icon name="ClipboardList" size={40} className="text-primary" />
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-2">Заявок не найдено</h3>
                <p className="text-gray-600">
                  {filterStatus === 'all' 
                    ? 'Здесь появятся заявки на электромонтажные работы' 
                    : filterStatus === 'new'
                    ? 'Новых заявок пока нет'
                    : filterStatus === 'responded'
                    ? 'Вы ещё не откликались на заявки'
                    : filterStatus === 'invited'
                    ? 'Вас ещё не приглашали на заявки'
                    : `В этом статусе нет заявок`
                  }
                </p>
              </Card>
            ) : (
              <div
                ref={parentRef}
                className="overflow-auto"
                style={{ height: 'calc(100vh - 280px)', minHeight: '600px' }}
              >
                <div
                  style={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    width: '100%',
                    position: 'relative',
                  }}
                >
                  {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const order = filteredOrders[virtualRow.index];
                    return (
                      <div
                        key={virtualRow.key}
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: `${virtualRow.size}px`,
                          transform: `translateY(${virtualRow.start}px)`,
                        }}
                      >
                        <div className="pb-4">
                          <AllOrderCard
                            order={order}
                            onViewDetails={setSelectedOrder}
                            updateOrderStatus={updateOrderStatus}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {permissions.isElectrician && (
              <div className="mt-6">
                <Button 
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
                  size="lg"
                  onClick={() => navigate('/orders')}
                >
                  <Icon name="Briefcase" size={20} className="mr-2" />
                  Смотреть мои заказы
                </Button>
              </div>
            )}

            {permissions.isAdmin && (
              <div className="mt-4">
                <Button 
                  className="w-full"
                  variant="outline"
                  onClick={() => {
                    const testOrder = {
                      order_id: `TEST-${Date.now()}`,
                      customer_name: 'Тестовый клиент',
                      customer_phone: '+79991234567',
                      address: 'г. Калининград, ул. Тестовая, д. 1',
                      date: new Date().toISOString().split('T')[0],
                      time: '10:00',
                      total_amount: 5000,
                      items: [
                        { name: 'Установка розетки', price: 500, quantity: 2, category: 'outlet' },
                        { name: 'Установка выключателя', price: 400, quantity: 3, category: 'switch' },
                        { name: 'Прокладка кабеля', price: 100, quantity: 30, category: 'cable' }
                      ],
                      status: 'pending'
                    };
                    
                    fetch('https://functions.poehali.dev/fa59900f-ff39-40ef-99de-7d268159765e', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(testOrder)
                    })
                    .then(() => alert('Тестовая заявка отправлена в Планфикс'))
                    .catch(err => alert('Ошибка: ' + err.message));
                  }}
                >
                  <Icon name="TestTube" size={16} className="mr-2" />
                  Создать тестовую заявку для Планфикс
                </Button>
              </div>
            )}
          </div>
        </div>

        <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
        
        {selectedOrder && (
          <OrderDetailModal
            order={selectedOrder}
            onClose={() => setSelectedOrder(null)}
            onStatusChange={updateOrderStatus}
            onRepeatOrder={(order) => {
              clearCart();
              order.items.forEach(item => addToCart(item.product, item.quantity));
              navigate('/cart');
            }}
            onAssignExecutor={assignExecutor}
          />
        )}
      </div>
    </RoleGate>
  );
}