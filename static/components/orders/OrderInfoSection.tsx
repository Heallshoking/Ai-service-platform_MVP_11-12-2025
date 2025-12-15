import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';

interface OrderInfoSectionProps {
  order: Order;
  isEditing: boolean;
  onEdit: (field: keyof Order, value: string) => void;
  isAdmin?: boolean;
}

export default function OrderInfoSection({ order, isEditing, onEdit, isAdmin = false }: OrderInfoSectionProps) {
  return (
    <div className="space-y-4">
        {isAdmin && (
          <div>
            <label className="block text-sm font-medium mb-1 text-muted-foreground">Дата создания (только для администратора)</label>
            <div className="text-base font-medium bg-gray-50 p-3 rounded-lg border border-gray-200">
              {new Date(order.createdAt).toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        )}
        
        {order.preferredDate && (
          <div>
            <label className="block text-sm font-medium mb-1 text-muted-foreground">Дата начала работы</label>
            {isEditing ? (
              <Input 
                type="date" 
                value={order.preferredDate}
                onChange={(e) => onEdit('preferredDate', e.target.value)}
                className="font-medium"
              />
            ) : (
              <div className="text-base font-medium bg-blue-50 p-3 rounded-lg border border-blue-200 text-blue-900">
                {new Date(order.preferredDate).toLocaleDateString('ru-RU', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })}
              </div>
            )}
          </div>
        )}
        
        <div>
          <label className="block text-sm font-medium mb-1 text-muted-foreground">Адрес</label>
          {isEditing ? (
            <Input 
              value={order.address}
              onChange={(e) => onEdit('address', e.target.value)}
              className="font-medium"
            />
          ) : (
            <div className="text-base font-medium bg-gray-50 p-3 rounded-lg border border-gray-200">
              {order.address}
            </div>
          )}
        </div>
        
        {order.notes && (
          <div>
            <label className="block text-sm font-medium mb-1 text-muted-foreground">Комментарий</label>
            {isEditing ? (
              <Textarea 
                value={order.notes}
                onChange={(e) => onEdit('notes', e.target.value)}
                className="font-medium"
                rows={3}
              />
            ) : (
              <div className="text-base bg-amber-50 p-3 rounded-lg border border-amber-200">
                {order.notes}
              </div>
            )}
          </div>
        )}
      </div>
  );
}