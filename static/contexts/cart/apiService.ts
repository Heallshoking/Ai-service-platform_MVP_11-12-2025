import { Order, PaymentStatus } from '@/types/electrical';

const ORDERS_API_URL = 'https://functions.poehali.dev/011a42c8-fcaa-413f-b611-d66cb669ba4e';
const PLANFIX_API_URL = 'https://functions.poehali.dev/fa59900f-ff39-40ef-99de-7d268159765e';

export const loadOrdersFromApi = async (): Promise<any[]> => {
  const response = await fetch(ORDERS_API_URL);
  if (!response.ok) {
    throw new Error('Failed to load orders');
  }
  return await response.json();
};

export const saveOrderToApi = async (orderData: any): Promise<void> => {
  const response = await fetch(ORDERS_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  
  if (!response.ok) {
    throw new Error('Failed to save order to DB');
  }
};

export const syncOrderToPlanfix = async (planfixData: any): Promise<void> => {
  await fetch(PLANFIX_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(planfixData)
  });
};

export const updateOrderStatusInApi = async (orderId: string, status: Order['status']): Promise<void> => {
  await fetch(`${ORDERS_API_URL}?id=${orderId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
};

export const assignExecutorInApi = async (
  orderId: string,
  electricianId: string,
  electricianName: string
): Promise<void> => {
  await fetch(`${ORDERS_API_URL}?id=${orderId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      assigned_to: electricianId, 
      assigned_to_name: electricianName 
    })
  });
};
