import { useState, useEffect } from 'react';
import { toast } from '@/hooks/use-toast';
import { Service, Executor, services } from './types';

export function useIndexLogic() {
  const [activeTab, setActiveTab] = useState('home');
  const [servicesList, setServicesList] = useState(services);
  const [executorsList, setExecutorsList] = useState<Executor[]>([]);
  const [selectedExecutor, setSelectedExecutor] = useState<number | null>(null);
  
  const [scenario, setScenario] = useState<'A' | 'B' | null>(null);
  const [repairType, setRepairType] = useState('');
  const [calcType, setCalcType] = useState('simple');
  const [switchCount, setSwitchCount] = useState(5);
  const [socketCount, setSocketCount] = useState(10);
  const [lightingType, setLightingType] = useState('');
  const [powerEquipment, setPowerEquipment] = useState<string[]>([]);
  const [installType, setInstallType] = useState('');
  const [hasWires, setHasWires] = useState('');
  
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [notes, setNotes] = useState('');

  const updateQuantity = (serviceId: string, change: number) => {
    setServicesList(prev => prev.map(s => {
      if (s.id === serviceId) {
        const newQty = Math.max(0, (s.quantity || 0) + change);
        return { ...s, quantity: newQty };
      }
      return s;
    }));
  };

  const getTotalPrice = () => {
    return servicesList.reduce((sum, s) => sum + (s.price * (s.quantity || 0)), 0);
  };

  const getTotalItems = () => {
    return servicesList.reduce((sum, s) => sum + (s.quantity || 0), 0);
  };

  const getCartItems = () => {
    return servicesList.filter(s => (s.quantity || 0) > 0);
  };

  useEffect(() => {
    const fetchExecutors = async () => {
      try {
        const response = await fetch('https://functions.poehali.dev/46dcbdcd-c306-4a31-b776-f6e34eba609f');
        const data = await response.json();
        if (data.executors) {
          setExecutorsList(data.executors);
        }
      } catch (error) {
        console.error('Error fetching executors:', error);
      }
    };
    fetchExecutors();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const cartItems = getCartItems();
    if (cartItems.length === 0) {
      toast({
        title: "Ошибка",
        description: "Добавьте услуги в заявку",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await fetch('https://functions.poehali.dev/5c3c68df-2e41-4012-81fd-e134547810fb', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: Date.now(),
          client_name: 'Клиент из веб-формы',
          phone,
          address,
          services: cartItems.map(item => ({
            service_id: parseInt(item.id),
            quantity: item.quantity || 1,
            price: item.price
          })),
          scheduled_date: date,
          scheduled_time: time,
          notes,
          executor_id: selectedExecutor
        })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "Заявка создана!",
          description: `Номер заявки: #${data.order_id}. Мы свяжемся с вами в ближайшее время.`
        });
        
        setTimeout(() => {
          window.open('https://t.me/konigelectric', '_blank');
        }, 1500);
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось отправить заявку. Попробуйте позже.",
        variant: "destructive"
      });
    }
  };

  return {
    activeTab,
    setActiveTab,
    servicesList,
    executorsList,
    selectedExecutor,
    setSelectedExecutor,
    scenario,
    setScenario,
    repairType,
    setRepairType,
    calcType,
    setCalcType,
    switchCount,
    setSwitchCount,
    socketCount,
    setSocketCount,
    lightingType,
    setLightingType,
    powerEquipment,
    setPowerEquipment,
    installType,
    setInstallType,
    hasWires,
    setHasWires,
    phone,
    setPhone,
    address,
    setAddress,
    date,
    setDate,
    time,
    setTime,
    notes,
    setNotes,
    updateQuantity,
    getTotalPrice,
    getTotalItems,
    getCartItems,
    handleSubmit
  };
}
