import { Order, ExecutorEarnings, ElectricalItem } from '@/types/electrical';

const WIRING_COMPLEX_SERVICES = [
  'блок из 5 розеток',
  'перенос газовых детекторов',
  'блок из 4-х розеток',
  'блок из 3-х розеток',
  'выключатель перенести',
  'блок из 2-х розеток',
  'добавить розетку',
  'бокс скрытого монтажа',
  'установка электросчётчика',
  'замена автомата',
  'бокс открытого монтажа',
  'установка автомата защиты',
  'новый вводной кабель',
  'монтаж кабеля',
  'электрика для квартиры'
];

export function isWiringComplexService(item: ElectricalItem): boolean {
  const itemName = item.name.toLowerCase();
  
  return WIRING_COMPLEX_SERVICES.some(service => 
    itemName.includes(service)
  );
}

export function calculateExecutorEarnings(order: Order): ExecutorEarnings {
  let wiringComplexAmount = 0;
  let otherServicesAmount = 0;
  
  order.items.forEach(item => {
    const itemTotal = item.price * item.quantity;
    
    if (isWiringComplexService(item)) {
      wiringComplexAmount += itemTotal;
    } else {
      otherServicesAmount += itemTotal;
    }
  });
  
  const wiringComplexEarnings = wiringComplexAmount * 0.3;
  const otherServicesEarnings = otherServicesAmount * 0.5;
  const executorEarnings = wiringComplexEarnings + otherServicesEarnings;
  const totalAmount = wiringComplexAmount + otherServicesAmount;
  
  return {
    orderId: order.id,
    totalAmount,
    installationWorkAmount: wiringComplexAmount,
    productAmount: otherServicesAmount,
    executorEarnings,
    installationEarnings: wiringComplexEarnings,
    productEarnings: otherServicesEarnings
  };
}

export function calculateTotalEarnings(
  orders: Order[],
  executorId: string,
  startDate?: Date,
  endDate?: Date
): {
  totalOrders: number;
  completedOrders: number;
  totalEarnings: number;
  expectedEarnings: number;
  installationEarnings: number;
  productEarnings: number;
} {
  const filteredOrders = orders.filter(order => {
    if (order.assignedTo !== executorId) return false;
    
    if (startDate || endDate) {
      const orderDate = new Date(order.createdAt);
      if (startDate && orderDate < startDate) return false;
      if (endDate && orderDate > endDate) return false;
    }
    
    return true;
  });
  
  let totalEarnings = 0;
  let expectedEarnings = 0;
  let installationEarnings = 0;
  let productEarnings = 0;
  let completedOrders = 0;
  
  filteredOrders.forEach(order => {
    const earnings = calculateExecutorEarnings(order);
    
    if (order.status === 'completed') {
      totalEarnings += earnings.executorEarnings;
      completedOrders++;
    } else if (order.status === 'in-progress' || order.status === 'confirmed') {
      expectedEarnings += earnings.executorEarnings;
    }
    
    installationEarnings += earnings.installationEarnings;
    productEarnings += earnings.productEarnings;
  });
  
  return {
    totalOrders: filteredOrders.length,
    completedOrders,
    totalEarnings,
    expectedEarnings,
    installationEarnings,
    productEarnings
  };
}