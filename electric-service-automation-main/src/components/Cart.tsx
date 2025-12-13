import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { Service } from '@/types/services';

interface CartItem {
  service: Service;
  quantity: number;
}

interface CartProps {
  items: CartItem[];
  onUpdateQuantity: (serviceId: string, quantity: number) => void;
  onRemove: (serviceId: string) => void;
}

const Cart = ({ items, onUpdateQuantity, onRemove }: CartProps) => {
  const getTotal = () => {
    return items.reduce((sum, item) => sum + (item.service.price * item.quantity), 0);
  };

  if (items.length === 0) {
    return null;
  }

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between pb-2 border-b">
        <h3 className="font-semibold flex items-center gap-2">
          <Icon name="ShoppingCart" size={18} />
          Список задач
        </h3>
        <span className="text-sm text-muted-foreground">{items.length}</span>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {items.map(item => (
          <div key={item.service.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{item.service.name}</p>
              <p className="text-xs text-muted-foreground">{item.service.price.toLocaleString()} ₽</p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8"
                onClick={() => onUpdateQuantity(item.service.id, Math.max(1, item.quantity - 1))}
              >
                <Icon name="Minus" size={14} />
              </Button>
              <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8"
                onClick={() => onUpdateQuantity(item.service.id, item.quantity + 1)}
              >
                <Icon name="Plus" size={14} />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onRemove(item.service.id)}
              >
                <Icon name="X" size={16} />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="pt-2 border-t">
        <div className="flex items-center justify-between font-semibold">
          <span>Итого:</span>
          <span className="text-lg">{getTotal().toLocaleString()} ₽</span>
        </div>
      </div>
    </Card>
  );
};

export default Cart;
