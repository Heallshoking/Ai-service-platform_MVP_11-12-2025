import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';

interface OrderInfoCompactSectionProps {
  order: Order;
  isElectrician?: boolean;
}

const canAccessPhone = (order: Order): boolean => {
  if (!order.departureConfirmedAt) return false;
  const twentyMinutes = 20 * 60 * 1000;
  const timeElapsed = Date.now() - order.departureConfirmedAt;
  return timeElapsed >= twentyMinutes;
};

const getYandexNavigatorUrl = (address: string): string => {
  const encodedAddress = encodeURIComponent(address);
  return `https://yandex.ru/maps/?q=${encodedAddress}`;
};

export default function OrderInfoCompactSection({ order, isElectrician = false }: OrderInfoCompactSectionProps) {
  const phoneAccessGranted = isElectrician ? canAccessPhone(order) : true;
  const navUrl = getYandexNavigatorUrl(order.address);

  return (
    <div className="flex flex-wrap gap-2">
      <a
        href={navUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition-colors text-sm font-medium"
        title="Открыть в Яндекс.Навигаторе"
      >
        <Icon name="MapPin" size={16} />
        {order.address}
      </a>

      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg border border-gray-200 text-sm font-medium">
        <Icon name="User" size={16} />
        {order.customerName}
      </div>

      {phoneAccessGranted ? (
        <a
          href={`tel:${order.customerPhone}`}
          className="flex items-center gap-2 px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg border border-green-200 transition-colors text-sm font-medium"
        >
          <Icon name="Phone" size={16} />
          {order.customerPhone}
        </a>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 text-amber-700 rounded-lg border border-amber-200 text-sm font-medium">
          <Icon name="Lock" size={16} />
          Телефон скоро откроется
        </div>
      )}
    </div>
  );
}
