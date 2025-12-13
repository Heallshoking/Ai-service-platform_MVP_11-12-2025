import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';

interface Electrician {
  id: string;
  name: string;
  phone: string;
  rating?: number;
  completedOrders?: number;
}

interface AssignExecutorSelectorProps {
  order: Order;
  onAssign: (orderId: string, electricianId: string, electricianName: string) => void;
}

const MOCK_ELECTRICIANS: Electrician[] = [
  { id: 'electrician-1', name: 'Петр Электрик', phone: '89000000002', rating: 4.8, completedOrders: 45 },
  { id: 'electrician-2', name: 'Сергей Мастер', phone: '89000000004', rating: 4.9, completedOrders: 38 },
  { id: 'electrician-3', name: 'Иван Профи', phone: '89000000005', rating: 4.7, completedOrders: 52 }
];

export default function AssignExecutorSelector({ order, onAssign }: AssignExecutorSelectorProps) {
  const [selectedElectrician, setSelectedElectrician] = useState<string>(order.assignedTo || '');
  const [isAssigning, setIsAssigning] = useState(false);

  useEffect(() => {
    setSelectedElectrician(order.assignedTo || '');
  }, [order.assignedTo]);

  const handleAssign = () => {
    if (!selectedElectrician) return;
    
    const electrician = MOCK_ELECTRICIANS.find(e => e.id === selectedElectrician);
    if (electrician) {
      setIsAssigning(true);
      onAssign(order.id, electrician.id, electrician.name);
      setTimeout(() => setIsAssigning(false), 500);
    }
  };

  const handleUnassign = () => {
    setIsAssigning(true);
    onAssign(order.id, '', '');
    setSelectedElectrician('');
    setTimeout(() => setIsAssigning(false), 500);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon name="User" size={18} className="text-primary" />
        <h3 className="font-semibold text-sm">Назначить исполнителя</h3>
      </div>

      {order.assignedTo ? (
        <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold">
            {order.assignedToName?.charAt(0) || 'М'}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-sm">{order.assignedToName || 'Мастер'}</p>
            <p className="text-xs text-muted-foreground">Назначен исполнитель</p>
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={handleUnassign}
            disabled={isAssigning}
          >
            <Icon name="X" size={16} className="mr-1" />
            Снять
          </Button>
        </div>
      ) : (
        <div className="flex gap-2">
          <Select value={selectedElectrician} onValueChange={setSelectedElectrician}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Выберите мастера" />
            </SelectTrigger>
            <SelectContent>
              {MOCK_ELECTRICIANS.map(electrician => (
                <SelectItem key={electrician.id} value={electrician.id}>
                  <div className="flex items-center gap-2">
                    <span>{electrician.name}</span>
                    {electrician.rating && (
                      <span className="text-xs text-yellow-600 flex items-center gap-1">
                        <Icon name="Star" size={12} />
                        {electrician.rating}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            onClick={handleAssign} 
            disabled={!selectedElectrician || isAssigning}
            size="sm"
          >
            <Icon name="Check" size={16} className="mr-1" />
            Назначить
          </Button>
        </div>
      )}
    </div>
  );
}
