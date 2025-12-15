import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import ExecutorSelect from '@/components/ExecutorSelect';
import { Service, Executor } from './types';

interface OrderTabProps {
  phone: string;
  setPhone: (phone: string) => void;
  address: string;
  setAddress: (address: string) => void;
  date: string;
  setDate: (date: string) => void;
  time: string;
  setTime: (time: string) => void;
  notes: string;
  setNotes: (notes: string) => void;
  selectedExecutor: number | null;
  setSelectedExecutor: (id: number | null) => void;
  executorsList: Executor[];
  getCartItems: () => Service[];
  getTotalPrice: () => number;
  handleSubmit: (e: React.FormEvent) => void;
}

export default function OrderTab({
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
  selectedExecutor,
  setSelectedExecutor,
  executorsList,
  getCartItems,
  getTotalPrice,
  handleSubmit
}: OrderTabProps) {
  const cartItems = getCartItems();

  return (
    <div className="space-y-6 animate-fade-in pb-24">
      <div className="text-center space-y-2">
        <h2 className="font-heading text-2xl md:text-3xl font-bold text-foreground">
          Оформление заявки
        </h2>
        <p className="text-muted-foreground text-sm">Заполните данные для связи</p>
      </div>

      {cartItems.length === 0 ? (
        <Card className="p-8 text-center bg-card">
          <Icon name="ShoppingCart" size={48} className="mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Добавьте услуги в заявку</p>
        </Card>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card className="p-6 bg-card space-y-4">
            <h3 className="font-semibold text-lg">Выбранные услуги</h3>
            {cartItems.map((item) => (
              <div key={item.id} className="flex justify-between items-center py-2 border-b last:border-0">
                <div className="flex-1">
                  <p className="font-medium text-sm">{item.title}</p>
                  <p className="text-xs text-muted-foreground">x{item.quantity}</p>
                </div>
                <p className="font-bold text-primary">{(item.price * (item.quantity || 1)).toLocaleString('ru-RU')} ₽</p>
              </div>
            ))}
            <div className="pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-lg">Итого:</span>
                <span className="text-2xl font-bold text-primary">{getTotalPrice().toLocaleString('ru-RU')} ₽</span>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-card space-y-4">
            <h3 className="font-semibold text-lg">Контактные данные</h3>
            <div className="space-y-2">
              <Label htmlFor="phone">Телефон *</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+7 (999) 123-45-67"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Адрес</Label>
              <Input
                id="address"
                placeholder="Улица, дом, квартира"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>
          </Card>

          <Card className="p-6 bg-card space-y-4">
            <h3 className="font-semibold text-lg">Дата и время</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="date">Дата</Label>
                <Input
                  id="date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="time">Время</Label>
                <Input
                  id="time"
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Комментарий</Label>
              <Textarea
                id="notes"
                placeholder="Дополнительная информация"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
          </Card>

          <ExecutorSelect
            executors={executorsList}
            selectedId={selectedExecutor}
            onSelect={setSelectedExecutor}
          />

          <Button type="submit" size="lg" className="w-full">
            <Icon name="Send" size={18} className="mr-2" />
            Отправить заявку
          </Button>
        </form>
      )}
    </div>
  );
}
