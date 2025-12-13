import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CartItem, Product, Order, ServiceOption, Payment, PaymentStatus, calculateExecutorEarnings, updateExecutorProfileAfterOrder } from '@/types/electrical';
import { useNotifications } from './NotificationContext';
import { useAuth } from './AuthContext';
import { sendOrderNotification, sendStatusUpdateNotification } from '@/lib/emailNotifications';
import {
  addItemToCart,
  removeItemFromCart,
  updateItemQuantity,
  updateItemOption,
  toggleItemAdditionalOption
} from './cart/cartOperations';
import {
  createOrderFromCart,
  updateOrderInList,
  addPaymentToOrder,
  updatePaymentInOrder,
  formatOrderForDatabase,
  formatOrderForPlanfix,
  parseOrderFromDatabase
} from './cart/orderOperations';
import {
  loadOrdersFromApi,
  saveOrderToApi,
  syncOrderToPlanfix,
  updateOrderStatusInApi,
  assignExecutorInApi
} from './cart/apiService';

interface CartContextType {
  cart: CartItem[];
  addToCart: (product: Product, quantity?: number, option?: ServiceOption, additionalOptions?: string[]) => void;
  removeFromCart: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  updateOption: (productId: string, option: ServiceOption) => void;
  toggleAdditionalOption: (productId: string, optionId: string) => void;
  clearCart: () => void;
  orders: Order[];
  createOrder: (orderData: Omit<Order, 'id' | 'items' | 'createdAt' | 'totalSwitches' | 'totalOutlets' | 'totalPoints' | 'estimatedCable' | 'estimatedFrames'>) => Order;
  updateOrderStatus: (orderId: string, status: Order['status']) => void;
  updateOrder: (order: Order) => void;
  assignExecutor: (orderId: string, electricianId: string, electricianName: string) => void;
  addPayment: (orderId: string, payment: Omit<Payment, 'id' | 'createdAt'>) => void;
  updatePaymentStatus: (orderId: string, paymentId: string, status: PaymentStatus) => void;
  markOrderAsViewed: (orderId: string, userId: string) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const notificationsContext = useNotifications();
  const { updateUser, getExecutorProfile } = useAuth();
  
  const [cart, setCart] = useState<CartItem[]>(() => {
    const saved = localStorage.getItem('electrical-cart');
    return saved ? JSON.parse(saved) : [];
  });

  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoaded, setOrdersLoaded] = useState(false);

  useEffect(() => {
    const loadOrders = async () => {
      try {
        const dbOrders = await loadOrdersFromApi();
        let formattedOrders: Order[] = dbOrders.map(parseOrderFromDatabase);
        
        if (formattedOrders.length < 5) {
          const mockOrdersNeeded = 5 - formattedOrders.length;
          const mockOrders: Order[] = Array.from({ length: mockOrdersNeeded }, (_, i) => ({
            id: `demo-${Date.now()}-${i}`,
            items: [
              { name: 'Установить розетку', price: 500, quantity: 2, category: 'установка' },
              { name: 'Установить выключатель', price: 400, quantity: 1, category: 'установка' }
            ],
            status: ['pending', 'confirmed', 'in-progress'][i % 3] as Order['status'],
            phone: '+7 (999) 123-45-67',
            address: 'Калининград, демо-адрес',
            createdAt: Date.now() - (i * 86400000),
            totalAmount: 1400,
            totalSwitches: 1,
            totalOutlets: 2,
            totalPoints: 3,
            estimatedCable: 15,
            estimatedFrames: 3,
            isDemo: true
          }));
          
          formattedOrders = [...formattedOrders, ...mockOrders];
        }
        
        setOrders(formattedOrders);
      } catch (err) {
        console.error('Failed to load orders from DB:', err);
        const saved = localStorage.getItem('electrical-orders');
        if (saved) {
          setOrders(JSON.parse(saved));
        }
      }
      setOrdersLoaded(true);
    };

    loadOrders();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem('electrical-cart', JSON.stringify(cart));
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [cart]);

  useEffect(() => {
    if (ordersLoaded) {
      const timeoutId = setTimeout(() => {
        localStorage.setItem('electrical-orders', JSON.stringify(orders));
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [orders, ordersLoaded]);

  const addToCart = (product: Product, quantity = 1, option: ServiceOption = 'install-only', additionalOptions?: string[]) => {
    setCart(prev => addItemToCart(prev, product, quantity, option, additionalOptions));
  };

  const removeFromCart = (productId: string) => {
    setCart(prev => removeItemFromCart(prev, productId));
  };

  const updateQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prev => updateItemQuantity(prev, productId, quantity));
  };

  const updateOption = (productId: string, option: ServiceOption) => {
    setCart(prev => updateItemOption(prev, productId, option));
  };

  const toggleAdditionalOption = (productId: string, optionId: string) => {
    setCart(prev => toggleItemAdditionalOption(prev, productId, optionId));
  };

  const clearCart = () => {
    setCart([]);
  };

  const createOrder = (orderData: Omit<Order, 'id' | 'items' | 'createdAt' | 'totalSwitches' | 'totalOutlets' | 'totalPoints' | 'estimatedCable' | 'estimatedFrames'>) => {
    const newOrder = createOrderFromCart(cart, orderData);

    setOrders(prev => [newOrder, ...prev]);
    clearCart();
    
    const dbOrderData = formatOrderForDatabase(newOrder);
    saveOrderToApi(dbOrderData).catch(err => 
      console.error('DB save failed:', err)
    );
    
    const planfixData = formatOrderForPlanfix(newOrder);
    syncOrderToPlanfix(planfixData).catch(err => 
      console.error('Planfix sync failed:', err)
    );
    
    sendOrderNotification(newOrder).catch(err =>
      console.error('Email notification failed:', err)
    );
    
    if (notificationsContext) {
      notificationsContext.addNotification({
        type: 'new_order',
        orderId: newOrder.id,
        title: 'Заявка создана',
        message: `Заявка #${newOrder.id.slice(-6)} успешно создана и отправлена на обработку`
      });
    }
    
    return newOrder;
  };

  const updateOrderStatus = (orderId: string, status: Order['status']) => {
    const statusMessages = {
      'pending': 'ожидает подтверждения',
      'confirmed': 'подтверждена и принята в работу',
      'on-the-way': 'мастер в пути',
      'arrived': 'мастер прибыл',
      'in-progress': 'начата, мастер приступил к работе',
      'completed': 'завершена'
    };

    const notificationTitles = {
      'pending': 'Поиск мастера',
      'confirmed': '✅ Заявка подтверждена',
      'on-the-way': '🚗 Мастер в пути',
      'arrived': '✅ Мастер прибыл',
      'in-progress': '🔧 Работа началась',
      'completed': '🎉 Работа завершена'
    };
    
    const order = orders.find(o => o.id === orderId);
    const oldStatus = order?.status || 'pending';
    
    setOrders(prev => updateOrderInList(prev, orderId, { status }));
    
    updateOrderStatusInApi(orderId, status).catch(err => 
      console.error('Failed to update order status in DB:', err)
    );
    
    if (order) {
      sendStatusUpdateNotification({ ...order, status }, oldStatus).catch(err =>
        console.error('Email notification failed:', err)
      );
    }
    
    if (status === 'completed') {
      const order = orders.find(o => o.id === orderId);
      const executorProfile = getExecutorProfile();
      
      if (order && executorProfile) {
        const earnings = calculateExecutorEarnings(order, executorProfile);
        const updatedProfile = updateExecutorProfileAfterOrder(executorProfile, earnings);
        
        updateUser({
          rank: updatedProfile.rank,
          completedOrders: updatedProfile.completedOrders,
          totalRevenue: updatedProfile.totalRevenue,
          isPro: updatedProfile.isPro,
          proUnlockedAt: updatedProfile.proUnlockedAt
        });
        
        if (notificationsContext) {
          notificationsContext.addNotification({
            type: 'info',
            orderId: orderId,
            title: 'Доход начислен',
            message: `Вы заработали ${earnings.executorEarnings.toLocaleString()} ₽ за заказ #${orderId.slice(-6)}`
          });
          
          if (updatedProfile.rank !== executorProfile.rank) {
            notificationsContext.addNotification({
              type: 'info',
              orderId: orderId,
              title: 'Повышение звания!',
              message: `Поздравляем! Вы получили новое звание: ${updatedProfile.rank}`
            });
          }
        }
      }
    }
    
    if (notificationsContext && oldStatus !== status) {
      const priority = ['on-the-way', 'arrived', 'completed'].includes(status) ? 'high' : 'normal';
      
      notificationsContext.addNotification({
        type: 'status_change',
        orderId: orderId,
        newStatus: status,
        title: notificationTitles[status] || 'Статус заявки изменен',
        message: `Заявка #${orderId.slice(-6)} ${statusMessages[status] || 'обновлена'}`,
        priority: priority as any
      });
    }
  };

  const assignExecutor = (orderId: string, electricianId: string, electricianName: string) => {
    setOrders(prev => 
      updateOrderInList(prev, orderId, { 
        assignedTo: electricianId, 
        assignedToName: electricianName 
      })
    );
    
    assignExecutorInApi(orderId, electricianId, electricianName).catch(err => 
      console.error('Failed to assign executor in DB:', err)
    );
    
    if (notificationsContext && electricianId) {
      notificationsContext.addNotification({
        type: 'info',
        orderId: orderId,
        title: '👷 Исполнитель назначен',
        message: `На заявку #${orderId.slice(-6)} назначен мастер: ${electricianName}`,
        priority: 'high' as any
      });
    }
  };

  const addPayment = (orderId: string, paymentData: Omit<Payment, 'id' | 'createdAt'>) => {
    setOrders(prev =>
      prev.map(order => {
        if (order.id !== orderId) return order;
        return addPaymentToOrder(order, paymentData);
      })
    );

    if (notificationsContext) {
      notificationsContext.addNotification({
        type: 'info',
        orderId: orderId,
        title: 'Платеж добавлен',
        message: `Платеж на сумму ${paymentData.amount.toLocaleString()} ₽ добавлен к заявке #${orderId.slice(-6)}`
      });
    }
  };

  const updatePaymentStatus = (orderId: string, paymentId: string, status: PaymentStatus) => {
    setOrders(prev =>
      prev.map(order => {
        if (order.id !== orderId) return order;
        return updatePaymentInOrder(order, paymentId, status);
      })
    );
  };

  const updateOrder = (updatedOrder: Order) => {
    setOrders(prev => 
      prev.map(order => order.id === updatedOrder.id ? updatedOrder : order)
    );
  };

  const markOrderAsViewed = (orderId: string, userId: string) => {
    setOrders(prev => 
      prev.map(order => {
        if (order.id !== orderId) return order;
        if (order.viewedBy?.includes(userId)) return order;
        return {
          ...order,
          viewedBy: [...(order.viewedBy || []), userId]
        };
      })
    );
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        addToCart,
        removeFromCart,
        updateQuantity,
        updateOption,
        toggleAdditionalOption,
        clearCart,
        orders,
        createOrder,
        updateOrderStatus,
        updateOrder,
        assignExecutor,
        addPayment,
        updatePaymentStatus,
        markOrderAsViewed
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
}