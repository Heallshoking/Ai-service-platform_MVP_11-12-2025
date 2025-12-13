import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import Icon from '@/components/ui/icon';
import OrderProgressBar from '@/components/OrderProgressBar';
import { toast } from '@/hooks/use-toast';

interface Executor {
  id: number;
  name: string;
  rating: number;
  specialization: string[];
  completedOrders: number;
  avatar?: string;
}

const mockExecutors: Executor[] = [
  {
    id: 1,
    name: 'Алексей Иванов',
    rating: 4.9,
    specialization: ['Электропроводка', 'Освещение', 'Розетки'],
    completedOrders: 156
  },
  {
    id: 2,
    name: 'Дмитрий Петров',
    rating: 4.8,
    specialization: ['Электрощитки', 'Автоматика'],
    completedOrders: 98
  },
  {
    id: 3,
    name: 'Сергей Смирнов',
    rating: 4.7,
    specialization: ['Монтаж', 'Диагностика'],
    completedOrders: 67
  }
];

const timeSlots = [
  '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', 
  '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'
];

const Schedule = () => {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedExecutor, setSelectedExecutor] = useState<number>(1);
  const [showExecutorList, setShowExecutorList] = useState(false);
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [contactPhone, setContactPhone] = useState('');

  const executor = mockExecutors.find(e => e.id === selectedExecutor) || mockExecutors[0];

  const handleSubmit = () => {
    if (!contactPhone.trim()) {
      toast({
        title: "Укажите телефон",
        description: "Телефон нужен для связи с мастером",
        variant: "destructive"
      });
      return;
    }

    if (!selectedDate) {
      toast({
        title: "Выберите дату",
        description: "Укажите дату визита",
        variant: "destructive"
      });
      return;
    }

    if (!selectedTime) {
      toast({
        title: "Выберите время",
        description: "Укажите удобное время визита",
        variant: "destructive"
      });
      return;
    }

    toast({
      title: "Заявка отправлена!",
      description: "Мастер свяжется с вами для подтверждения"
    });

    setTimeout(() => {
      navigate('/confirmation');
    }, 1500);
  };

  const handleViewExecutorProfile = (executorId: number) => {
    navigate(`/executor-public-profile?id=${executorId}`);
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <Button variant="ghost" onClick={() => navigate('/tasks')} className="gap-2">
              <Icon name="ArrowLeft" size={20} />
              Назад
            </Button>
            <h1 className="font-heading font-bold text-lg">Уточнение деталей</h1>
            <Button variant="ghost" onClick={() => navigate('/order-history')} className="text-sm">
              История
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          <OrderProgressBar currentStatus="scheduled" />

          <Card className="p-5">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="Phone" size={20} className="text-primary" />
              Контакты и детали
            </h2>
            
            <div className="space-y-3">
              <div>
                <Label htmlFor="phone" className="text-sm mb-1.5 block">Телефон для связи *</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+7 (___) ___-__-__"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="h-11"
                />
              </div>

              <div>
                <Label htmlFor="notes" className="text-sm mb-1.5 block">
                  Комментарий (адрес, этаж, пожелания)
                </Label>
                <Textarea
                  id="notes"
                  placeholder="Например: ул. Ленина 10, кв. 5, 2 этаж..."
                  value={additionalNotes}
                  onChange={(e) => setAdditionalNotes(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="Calendar" size={20} className="text-primary" />
              Дата и время встречи
            </h2>
            
            <div className="space-y-4">
              <div className="flex justify-center">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
                  className="rounded-md border"
                />
              </div>

              {selectedDate && (
                <div className="space-y-3">
                  <div className="p-3 bg-primary/5 rounded-lg">
                    <p className="text-sm font-semibold">
                      {selectedDate.toLocaleDateString('ru-RU', { 
                        weekday: 'long', 
                        day: 'numeric',
                        month: 'long'
                      })}
                    </p>
                  </div>

                  <div className="grid grid-cols-4 gap-2">
                    {timeSlots.map((time) => (
                      <Button
                        key={time}
                        variant={selectedTime === time ? 'default' : 'outline'}
                        onClick={() => setSelectedTime(time)}
                        className="h-11 font-semibold"
                      >
                        {time}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="User" size={20} className="text-primary" />
              Выберите специалиста
            </h2>
            
            {!showExecutorList ? (
              <div className="border-2 rounded-lg p-4 hover:border-primary/50 transition-all">
                <div className="flex items-center gap-3 mb-3">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                      {executor.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div className="flex-1">
                    <h3 className="font-bold text-base">{executor.name}</h3>
                    <div className="flex items-center gap-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Icon name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                        <span className="font-semibold">{executor.rating}</span>
                      </div>
                      <span className="text-muted-foreground">
                        • {executor.completedOrders} заказов
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="flex-1"
                    onClick={() => handleViewExecutorProfile(executor.id)}
                  >
                    <Icon name="Eye" size={16} className="mr-2" />
                    Профиль
                  </Button>
                  <Button 
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => setShowExecutorList(true)}
                  >
                    <Icon name="Users" size={16} className="mr-2" />
                    Другой мастер
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {mockExecutors.map((exec) => (
                  <div
                    key={exec.id}
                    className={`border-2 rounded-lg p-3 cursor-pointer transition-all ${
                      selectedExecutor === exec.id ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => {
                      setSelectedExecutor(exec.id);
                      setShowExecutorList(false);
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <Avatar className="h-12 w-12">
                        <AvatarFallback className="bg-primary/10 text-primary">
                          {exec.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm">{exec.name}</h3>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Icon name="Star" size={12} className="text-yellow-500 fill-yellow-500" />
                            <span>{exec.rating}</span>
                          </div>
                          <span>• {exec.completedOrders} заказов</span>
                        </div>
                      </div>

                      {selectedExecutor === exec.id && (
                        <Icon name="Check" size={20} className="text-primary" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </main>

      <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border shadow-lg z-50">
        <div className="container mx-auto px-4 py-4">
          <Button 
            size="lg" 
            className="w-full h-14 text-lg font-semibold shadow-lg gap-2"
            onClick={handleSubmit}
          >
            <Icon name="Send" size={22} />
            Отправить заявку
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Schedule;