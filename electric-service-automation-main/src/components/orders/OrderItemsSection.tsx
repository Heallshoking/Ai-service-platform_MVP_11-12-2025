import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { ElectricalItem } from '@/types/electrical';

interface OrderItemsSectionProps {
  items: ElectricalItem[];
  totalAmount: number;
  isEditing: boolean;
  onItemEdit: (index: number, field: keyof ElectricalItem, value: string | number) => void;
}

export default function OrderItemsSection({ items, totalAmount, isEditing, onItemEdit }: OrderItemsSectionProps) {
  const safeItems = items || [];
  const safeTotalAmount = totalAmount || 0;

  const cableItem = safeItems.find(item => 
    item.name.toLowerCase().includes('кабел') || 
    item.name.toLowerCase().includes('монтаж кабеля')
  );
  const cableMeters = cableItem ? cableItem.quantity : 0;
  const materialsCost = cableMeters * 130;

  return (
    <div className="space-y-2 font-mono text-sm">
      {safeItems.map((item, index) => {
        const itemPrice = item.price || 0;
        const itemQuantity = item.quantity || 1;
        const itemTotal = itemPrice * itemQuantity;

        return (
          <div key={index} className="border-b border-dashed border-gray-200 pb-2 mb-2">
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1">
                {isEditing ? (
                  <Input 
                    value={item.name}
                    onChange={(e) => onItemEdit(index, 'name', e.target.value)}
                    className="font-medium mb-1"
                  />
                ) : (
                  <span className="font-semibold text-gray-900 block">{item.name}</span>
                )}
                {item.description && !isEditing && (
                  <p className="text-xs text-gray-500 mt-1">{item.description}</p>
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center mt-2">
              <div className="flex items-center gap-3 text-xs text-gray-600">
                {isEditing ? (
                  <>
                    <Input 
                      type="number"
                      value={item.quantity}
                      onChange={(e) => onItemEdit(index, 'quantity', parseInt(e.target.value))}
                      className="w-16 h-7 text-xs"
                      min="1"
                    />
                    <span>×</span>
                    <Input 
                      type="number"
                      value={item.price}
                      onChange={(e) => onItemEdit(index, 'price', parseFloat(e.target.value))}
                      className="w-24 h-7 text-xs"
                    />
                  </>
                ) : (
                  <span>{itemQuantity} шт × {itemPrice.toLocaleString()} ₽</span>
                )}
              </div>
              <span className="font-bold text-gray-900">{itemTotal.toLocaleString()} ₽</span>
            </div>
          </div>
        );
      })}
      
      <div className="border-t-2 border-gray-800 pt-4 mt-6">
        <div className="flex justify-between items-center mb-3">
          <span className="font-bold text-xl text-gray-900">ИТОГО:</span>
          <span className="font-bold text-2xl text-primary">{safeTotalAmount.toLocaleString()} ₽</span>
        </div>
        {cableMeters > 0 && (
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200 mt-3">
            <div className="flex items-center gap-2 text-sm">
              <Icon name="Package" size={16} className="text-blue-600" />
              <span className="text-gray-700">Примерная стоимость материалов:</span>
              <span className="font-bold text-blue-700">{materialsCost.toLocaleString()} ₽</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}