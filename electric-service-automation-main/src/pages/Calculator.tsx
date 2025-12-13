import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { RoomType, ROOM_DEFAULTS, ROOM_LABELS } from '@/types/electrical';
import { useCart } from '@/contexts/CartContext';
import ContactModal from '@/components/ContactModal';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';

export default function Calculator() {
  const navigate = useNavigate();
  const { cart } = useCart();
  const [selectedRoom, setSelectedRoom] = useState<RoomType | ''>('');
  const [showContactModal, setShowContactModal] = useState(false);

  const defaults = selectedRoom ? ROOM_DEFAULTS[selectedRoom as RoomType] : null;
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />
        <div className="bg-white shadow-lg p-6 space-y-6">
          <h1 className="text-2xl font-bold text-gray-800">
            <span className="font-extrabold text-primary">Смета на электромонтаж</span>
            <br />
            <span className="text-lg text-gray-600">ЗА 2 МИНУТЫ</span>
          </h1>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block text-gray-700">Выберите тип объекта</label>
              <select
                value={selectedRoom}
                onChange={(e) => setSelectedRoom(e.target.value as RoomType | '')}
                className="w-full p-3 border-2 border-blue-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              >
                <option value="">-- Выберите тип --</option>
                {Object.entries(ROOM_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div className="mt-4">
              <img 
                src="https://cdn.poehali.dev/files/fc495206-a509-40b1-a08b-6bab202e2b18.jpg"
                alt="Профессиональный электрик"
                className="w-full h-48 object-cover rounded-lg shadow-md"
              />
              <div className="mt-3 text-center">
                <p className="text-sm text-gray-700">
                  👉 Задавайте вопросы в{' '}
                  <a 
                    href="https://t.me/konigelectric" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 font-semibold underline"
                  >
                    Telegram
                  </a>
                  {' '}❤️
                </p>
              </div>
            </div>

            {defaults && (
              <>
                <Card className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-blue-900">
                      📊 Среднее количество для {ROOM_LABELS[selectedRoom as RoomType].toLowerCase()}:
                    </p>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div className="bg-white p-3 rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-primary">{defaults.switches}</div>
                        <div className="text-xs text-muted-foreground">Выключателей</div>
                      </div>
                      <div className="bg-white p-3 rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-primary">{defaults.outlets}</div>
                        <div className="text-xs text-muted-foreground">Розеток</div>
                      </div>
                    </div>
                    <p className="text-xs text-blue-700 mt-2">
                      * Среднее значение. Выберите точное количество на следующем экране.
                    </p>
                  </div>
                </Card>

                <div className="space-y-3 pt-4">
                  <h3 className="font-semibold text-lg text-gray-800">Что дальше?</h3>
                  <div className="space-y-2">
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                        1
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Выберите нужные услуги и укажите количество
                      </p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                        2
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Проверьте план работ и уточните детали
                      </p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                        3
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Оформите заявку — мы свяжемся с вами
                      </p>
                    </div>
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon name="Phone" size={18} className="text-blue-600" />
                        <p className="font-semibold text-sm text-blue-900">Или свяжитесь с нами прямо сейчас</p>
                      </div>
                      <a 
                        href="tel:+74012520725"
                        className="text-xl font-bold text-blue-600 hover:text-blue-700"
                      >
                        +7 (4012) 52-07-25
                      </a>
                      <p className="text-xs text-muted-foreground mt-1">
                        Вызовите мастера на осмотр в Калининграде
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {defaults && (
          <div className="p-6">
            <Button
              size="lg"
              className="w-full font-semibold h-14 text-base shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              onClick={() => navigate('/products')}
            >
              Уточнить детали →
            </Button>
          </div>
        )}
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
    </div>
  );
}