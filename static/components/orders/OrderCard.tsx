import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Order, ElectricalItem, PaymentStatus } from '@/types/electrical';

interface OrderCardProps {
  order: Order;
  onViewDetails: (order: Order) => void;
  onRepeat: (order: Order) => void;
}

const STATUS_LABELS = {
  'pending': 'Поиск мастера',
  'confirmed': 'Подтверждена',
  'on-the-way': 'В пути',
  'arrived': 'Прибыл',
  'in-progress': 'В работе',
  'completed': 'Завершена'
};

const STATUS_COLORS = {
  'pending': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'confirmed': 'bg-blue-100 text-blue-800 border-blue-300',
  'on-the-way': 'bg-purple-100 text-purple-800 border-purple-300',
  'arrived': 'bg-indigo-100 text-indigo-800 border-indigo-300',
  'in-progress': 'bg-orange-100 text-orange-800 border-orange-300',
  'completed': 'bg-green-100 text-green-800 border-green-300'
};

const PAYMENT_STATUS_ICONS: Record<PaymentStatus, string> = {
  'unpaid': 'CircleDollarSign',
  'partially_paid': 'DollarSign',
  'paid': 'CheckCircle2',
  'refunded': 'RotateCcw',
  'pending': 'Clock'
};

const PAYMENT_STATUS_COLORS: Record<PaymentStatus, string> = {
  'unpaid': 'text-red-600',
  'partially_paid': 'text-yellow-600',
  'paid': 'text-green-600',
  'refunded': 'text-gray-600',
  'pending': 'text-blue-600'
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

const OrderCard = memo(({ order, onViewDetails, onRepeat }: OrderCardProps) => {
  return (
    <Card className="p-5 hover:shadow-lg transition-all cursor-pointer animate-fadeIn">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-lg text-gray-800 flex items-center gap-2">
              <Icon name="MapPin" size={18} className="text-primary" />
              {order.address || 'Адрес не указан'}
            </h3>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-semibold py-1 px-3 rounded-full border ${STATUS_COLORS[order.status]}`}>
              {STATUS_LABELS[order.status]}
            </span>
            <span className="text-xs text-gray-500">#{order.id.slice(-6)}</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {new Date(order.createdAt).toLocaleDateString('ru-RU', {
              day: 'numeric',
              month: 'long',
              year: 'numeric'
            })}
          </p>
          {order.assignedToName && (
            <div className="flex items-center gap-1 mt-2 text-xs text-green-700 bg-green-50 px-2 py-1 rounded-lg w-fit">
              <Icon name="User" size={12} />
              <span>{order.assignedToName}</span>
            </div>
          )}
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-primary">{(order.totalAmount || 0).toLocaleString()} ₽</p>
          <p className="text-xs text-gray-500">{order.items?.length || 0} услуг</p>
          {order.paymentStatus && (
            <div className="flex items-center justify-end gap-1 mt-1">
              <Icon 
                name={PAYMENT_STATUS_ICONS[order.paymentStatus] as any} 
                size={12} 
                className={PAYMENT_STATUS_COLORS[order.paymentStatus]} 
              />
              {order.paidAmount !== undefined && order.paidAmount > 0 && (
                <span className="text-xs text-gray-600">
                  {order.paidAmount.toLocaleString()} ₽
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <Button 
          variant="outline" 
          size="sm"
          className="flex-1"
          onClick={() => onViewDetails(order)}
        >
          <Icon name="Eye" size={16} className="mr-2" />
          Подробнее
        </Button>
        <Button 
          variant="outline" 
          size="sm"
          className="flex-1"
          onClick={(e) => {
            e.stopPropagation();
            onRepeat(order);
          }}
          title="Повторить заказ"
        >
          <Icon name="RefreshCw" size={16} className="mr-2" />
          Повторить
        </Button>
      </div>
    </Card>
  );
});

OrderCard.displayName = 'OrderCard';

export default OrderCard;