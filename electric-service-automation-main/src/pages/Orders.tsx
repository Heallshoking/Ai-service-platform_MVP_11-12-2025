import { useEffect, useState, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { Order, ElectricalItem } from '@/types/electrical';
import ContactModal from '@/components/ContactModal';
import ProductSelectionModal from '@/components/ProductSelectionModal';
import CalculatorModal from '@/components/CalculatorModal';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import OrderDetailModal from '@/components/orders/OrderDetailModal';
import OrderCard from '@/components/orders/OrderCard';
import EarningsWidget from '@/components/executor/EarningsWidget';
import ExecutorStatsCard from '@/components/executor/ExecutorStatsCard';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import { useDebounce } from '@/hooks/useDebounce';
import { useVirtualizer } from '@tanstack/react-virtual';

const STATUS_LABELS = {
  'pending': 'Поиск мастера',
  'confirmed': 'Подтверждена',
  'on-the-way': 'В пути',
  'arrived': 'Прибыл',
  'in-progress': 'В работе',
  'completed': 'Завершена'
};

export default function Orders() {
  const navigate = useNavigate();
  const location = useLocation();
  const { orders, clearCart, updateOrderStatus, addToCart, assignExecutor, markOrderAsViewed } = useCart();
  const { isAuthenticated } = useAuth();
  const permissions = usePermissions();

  // Redirect non-authenticated users to home
  if (!isAuthenticated) {
    navigate('/');
    return null;
  }
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showCalculatorModal, setShowCalculatorModal] = useState(false);
  
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const parentRef = useRef<HTMLDivElement>(null);

  const handleNewOrder = () => {
    clearCart();
    navigate('/products');
  };

  const handleRepeatOrder = (order: Order) => {
    clearCart();
    order.items.forEach(item => {
      addToCart(item);
    });
    navigate('/cart');
  };

  useEffect(() => {
    const newOrderId = location.state?.newOrderId;
    if (newOrderId) {
      const order = orders.find(o => o.id === newOrderId);
      if (order) {
        setSelectedOrder(order);
      }
    }
  }, [location.state, orders]);

  const { user, getExecutorProfile } = useAuth();
  const executorProfile = getExecutorProfile();

  const filteredOrders = useMemo(() => {
    const filtered = orders.filter(order => {
      if (!order || !order.items) return false;
      
      if (permissions.isElectrician && !permissions.isAdmin && user) {
        if (order.assignedTo !== user.id) return false;
      }
      
      if (statusFilter !== 'all' && order.status !== statusFilter) return false;
      
      if (debouncedSearchQuery) {
        const query = debouncedSearchQuery.toLowerCase();
        const matchesId = order.id?.toLowerCase().includes(query);
        const matchesAddress = order.address?.toLowerCase().includes(query);
        const matchesPhone = order.phone?.toLowerCase().includes(query);
        if (!matchesId && !matchesAddress && !matchesPhone) return false;
      }
      
      return true;
    });
    
    return filtered.sort((a, b) => {
      if (permissions.isElectrician && !permissions.isAdmin) {
        const dateA = a.scheduledDate ? new Date(a.scheduledDate).getTime() : a.createdAt;
        const dateB = b.scheduledDate ? new Date(b.scheduledDate).getTime() : b.createdAt;
        return dateA - dateB;
      } else {
        return b.createdAt - a.createdAt;
      }
    });
  }, [orders, statusFilter, debouncedSearchQuery, permissions, user]);

  const statusCounts = useMemo(() => {
    const counts = {
      all: orders.length,
      pending: 0,
      confirmed: 0,
      'in-progress': 0,
      completed: 0
    };
    
    orders.forEach(order => {
      if (order.status in counts) {
        counts[order.status as keyof typeof counts]++;
      }
    });
    
    return counts;
  }, [orders]);

  const unviewedPendingCount = useMemo(() => {
    if (!user) return 0;
    return orders.filter(order => 
      order.status === 'pending' && 
      !order.viewedBy?.includes(user.id)
    ).length;
  }, [orders, user]);

  useEffect(() => {
    if (statusFilter === 'pending' && user) {
      const pendingOrders = orders.filter(o => o.status === 'pending');
      pendingOrders.forEach(order => {
        if (!order.viewedBy?.includes(user.id)) {
          markOrderAsViewed(order.id, user.id);
        }
      });
    }
  }, [statusFilter, orders, user, markOrderAsViewed]);

  const rowVirtualizer = useVirtualizer({
    count: filteredOrders.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 180,
    overscan: 5,
  });

  const isSearching = searchQuery !== debouncedSearchQuery;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />
        
        <div className="bg-white shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Мои заказы</h1>
            </div>
            {orders.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="text-3xl font-bold text-primary">{orders.length}</div>
                  <div className="text-xs text-gray-500">заказов</div>
                </div>
              </div>
            )}
          </div>

          {orders.length > 0 && (
            <>
              <div className="relative mb-4">
                <Icon name="Search" size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10" />
                <Input
                  placeholder="Найти заказ..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-10"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <Icon name="X" size={16} />
                  </button>
                )}
                {isSearching && (
                  <Icon name="Loader2" size={16} className="absolute right-10 top-1/2 -translate-y-1/2 animate-spin text-primary" />
                )}
              </div>

              <Tabs value={statusFilter} onValueChange={setStatusFilter} className="w-full">
                <TabsList className="w-full grid grid-cols-5 h-auto">
                  <TabsTrigger value="all" className="flex-col py-2 px-1">
                    <span className="text-lg font-bold">{statusCounts.all}</span>
                    <span className="text-xs">Все</span>
                  </TabsTrigger>
                  <TabsTrigger value="pending" className="flex-col py-2 px-1 relative">
                    <span className="text-lg font-bold">{statusCounts.pending}</span>
                    <span className="text-xs">Новые</span>
                    {unviewedPendingCount > 0 && (
                      <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold shadow-lg animate-pulse">
                        {unviewedPendingCount}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="confirmed" className="flex-col py-2 px-1">
                    <span className="text-lg font-bold">{statusCounts.confirmed}</span>
                    <span className="text-xs">Принято</span>
                  </TabsTrigger>
                  <TabsTrigger value="in-progress" className="flex-col py-2 px-1">
                    <span className="text-lg font-bold">{statusCounts['in-progress']}</span>
                    <span className="text-xs">В работе</span>
                  </TabsTrigger>
                  <TabsTrigger value="completed" className="flex-col py-2 px-1">
                    <span className="text-lg font-bold">{statusCounts.completed}</span>
                    <span className="text-xs">Готово</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </>
          )}
        </div>

        <div className="p-6 space-y-4">
          {permissions.isElectrician && executorProfile && (
            <div className="space-y-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Мой профиль</h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => navigate('/executor-profile-settings')}
                  className="text-blue-600 hover:text-blue-700"
                >
                  <Icon name="Settings" className="h-4 w-4 mr-1" />
                  Настроить
                </Button>
              </div>
              <ExecutorStatsCard profile={executorProfile} />
              <EarningsWidget orders={orders} executorId={user?.uid || ''} />
            </div>
          )}

          {filteredOrders.length === 0 && orders.length > 0 && (
            <Card className="p-8 text-center">
              <Icon name="Search" size={48} className="mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Ничего не найдено</h3>
              <p className="text-gray-600 mb-4">
                {searchQuery ? 'Попробуйте изменить запрос поиска' : 'В этом статусе нет заявок'}
              </p>
              {(searchQuery || statusFilter !== 'all') && (
                <Button 
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                  }} 
                  variant="outline"
                >
                  Показать все заявки
                </Button>
              )}
            </Card>
          )}

          {filteredOrders.length === 0 && orders.length === 0 && (
            <Card className="p-8 text-center animate-fadeIn">
              <div className="mb-4">
                <div className="w-20 h-20 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
                  <Icon name="ClipboardList" size={40} className="text-primary" />
                </div>
              </div>
              <h3 className="text-xl font-bold mb-2">Здесь будут ваши заявки</h3>
              <p className="text-gray-600 mb-6">
                Создайте первую заявку на электромонтажные работы
              </p>
              <Button onClick={handleNewOrder} className="w-full" size="lg">
                <Icon name="Plus" size={20} className="mr-2" />
                Создать заявку
              </Button>
            </Card>
          )}

          {filteredOrders.length > 0 && (
            <div
              ref={parentRef}
              className="overflow-auto"
              style={{ height: 'calc(100vh - 320px)', minHeight: '500px' }}
            >
              <div className="mb-3 flex items-center justify-between px-1">
                <span className="text-sm text-gray-600">
                  {statusFilter === 'all' ? 'Все заявки' : STATUS_LABELS[statusFilter as keyof typeof STATUS_LABELS]}
                </span>
                <span className="text-sm font-medium text-gray-800">
                  {filteredOrders.length} {filteredOrders.length === 1 ? 'заявка' : filteredOrders.length < 5 ? 'заявки' : 'заявок'}
                </span>
              </div>
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
                        <OrderCard
                          order={order}
                          onViewDetails={setSelectedOrder}
                          onRepeat={handleRepeatOrder}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {orders.length > 0 && (
            <div className="mt-4">
              <Button 
                onClick={handleNewOrder}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-6 rounded-xl shadow-lg"
                size="lg"
              >
                <Icon name="Plus" size={20} className="mr-2" />
                Новая заявка
              </Button>
            </div>
          )}
        </div>
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
      {showProductModal && <ProductSelectionModal onClose={() => setShowProductModal(false)} />}
      {showCalculatorModal && <CalculatorModal onClose={() => setShowCalculatorModal(false)} />}
      
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onStatusChange={updateOrderStatus}
          onRepeatOrder={handleRepeatOrder}
          onAssignExecutor={assignExecutor}
        />
      )}
    </div>
  );
}