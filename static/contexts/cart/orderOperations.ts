import { Order, CartItem, calculateTotals, PaymentStatus, Payment } from '@/types/electrical';

export const createOrderFromCart = (
  cart: CartItem[],
  orderData: Omit<Order, 'id' | 'items' | 'createdAt' | 'totalSwitches' | 'totalOutlets' | 'totalPoints' | 'estimatedCable' | 'estimatedFrames'>
): Order => {
  const totals = calculateTotals(cart);
  
  const electricalItems = cart.map(cartItem => ({
    name: cartItem.product.name,
    price: cartItem.selectedOption === 'install-only' 
      ? cartItem.product.priceInstallOnly 
      : cartItem.product.priceWithWiring,
    quantity: cartItem.quantity,
    category: cartItem.product.category,
    description: cartItem.product.description
  }));
  
  const totalAmount = electricalItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  const newOrder: Order = {
    ...orderData,
    id: `ORD-${Date.now()}`,
    items: electricalItems,
    createdAt: Date.now(),
    totalAmount,
    ...totals
  };

  return newOrder;
};

export const updateOrderInList = (
  orders: Order[],
  orderId: string,
  updates: Partial<Order>
): Order[] => {
  return orders.map(order =>
    order.id === orderId ? { ...order, ...updates } : order
  );
};

export const calculatePaymentStatus = (totalAmount: number, paidAmount: number): PaymentStatus => {
  if (paidAmount === 0) return 'unpaid';
  if (paidAmount >= totalAmount) return 'paid';
  return 'partially_paid';
};

export const addPaymentToOrder = (
  order: Order,
  paymentData: Omit<Payment, 'id' | 'createdAt'>
): Order => {
  const newPayment: Payment = {
    ...paymentData,
    id: `pay-${Date.now()}-${Math.random()}`,
    createdAt: Date.now(),
  };

  const payments = [...(order.payments || []), newPayment];
  const paidAmount = payments
    .filter(p => p.status === 'paid')
    .reduce((sum, p) => sum + p.amount, 0);
  const totalAmount = order.totalAmount || 0;
  const paymentStatus = calculatePaymentStatus(totalAmount, paidAmount);

  return {
    ...order,
    payments,
    paidAmount,
    paymentStatus,
  };
};

export const updatePaymentInOrder = (
  order: Order,
  paymentId: string,
  status: PaymentStatus
): Order => {
  const payments = (order.payments || []).map(p =>
    p.id === paymentId ? { ...p, status } : p
  );

  const paidAmount = payments
    .filter(p => p.status === 'paid')
    .reduce((sum, p) => sum + p.amount, 0);
  const totalAmount = order.totalAmount || 0;
  const paymentStatus = calculatePaymentStatus(totalAmount, paidAmount);

  return {
    ...order,
    payments,
    paidAmount,
    paymentStatus,
  };
};

export const formatOrderForDatabase = (order: Order) => {
  return {
    order_uid: order.id,
    customer_name: order.customerName || 'Не указано',
    customer_phone: order.phone,
    customer_email: order.customerEmail || '',
    address: order.address,
    scheduled_date: order.date,
    scheduled_time: order.time,
    items: order.items,
    total_price: order.totalAmount,
    total_switches: order.totalSwitches,
    total_outlets: order.totalOutlets,
    total_points: order.totalPoints,
    estimated_cable: order.estimatedCable,
    estimated_frames: order.estimatedFrames,
    status: order.status,
    assigned_to: order.assignedTo || null,
    assigned_to_name: order.assignedToName || null,
    client_notes: order.notes || ''
  };
};

export const formatOrderForPlanfix = (order: Order) => {
  return {
    order_id: order.id,
    customer_name: order.customerName || 'Не указано',
    customer_phone: order.phone,
    address: order.address,
    date: order.date,
    time: order.time,
    total_amount: order.totalAmount,
    items: order.items,
    status: order.status
  };
};

export const parseOrderFromDatabase = (dbOrder: any): Order => {
  return {
    id: dbOrder.order_uid || `ORD-${dbOrder.id}`,
    customerName: dbOrder.customer_name || 'Не указано',
    customerPhone: dbOrder.customer_phone || dbOrder.phone || '',
    customerEmail: dbOrder.customer_email || '',
    date: dbOrder.scheduled_date || '',
    time: dbOrder.scheduled_time || '',
    address: dbOrder.address || '',
    phone: dbOrder.customer_phone || '',
    items: dbOrder.items || [],
    status: dbOrder.status || 'pending',
    totalSwitches: dbOrder.total_switches || 0,
    totalOutlets: dbOrder.total_outlets || 0,
    totalPoints: dbOrder.total_points || 0,
    estimatedCable: dbOrder.estimated_cable || 0,
    estimatedFrames: dbOrder.estimated_frames || 0,
    createdAt: new Date(dbOrder.created_at).getTime(),
    totalAmount: parseFloat(dbOrder.total_price || '0'),
    assignedTo: dbOrder.assigned_to,
    assignedToName: dbOrder.assigned_to_name,
    notes: dbOrder.client_notes,
    paymentStatus: dbOrder.payment_status,
    paidAmount: parseFloat(dbOrder.paid_amount || '0'),
    payments: dbOrder.payments
  };
};
