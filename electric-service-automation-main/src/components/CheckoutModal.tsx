import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { IMaskInput } from 'react-imask';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { calculateItemPrice, getDiscount, calculateFrames } from '@/types/electrical';

interface CheckoutModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CheckoutModal({ open, onClose }: CheckoutModalProps) {
  const navigate = useNavigate();
  const { cart, createOrder } = useCart();

  const [formData, setFormData] = useState({
    phone: '',
    address: '',
    date: '',
    time: ''
  });

  const [errors, setErrors] = useState({
    phone: '',
    address: '',
    date: '',
    time: ''
  });

  const [shakeField, setShakeField] = useState<string | null>(null);
  const phoneRef = useRef<HTMLDivElement>(null);
  const addressRef = useRef<HTMLDivElement>(null);
  const dateRef = useRef<HTMLDivElement>(null);
  const timeRef = useRef<HTMLDivElement>(null);

  const validateForm = () => {
    const newErrors = {
      phone: '',
      address: '',
      date: '',
      time: ''
    };

    if (!formData.phone || formData.phone.replace(/[^0-9]/g, '').length < 11) {
      newErrors.phone = 'Укажите номер телефона';
    }



    setErrors(newErrors);
    return !Object.values(newErrors).some(err => err);
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      // Find first field with error and scroll to it
      const newErrors = {
        phone: !formData.phone ? 'Укажите номер телефона' : (!/^\+?[0-9]{10,15}$/.test(formData.phone.replace(/\s/g, '')) ? 'Некорректный формат телефона' : ''),
        address: !formData.address ? 'Укажите адрес' : '',
        date: !formData.date ? 'Выберите дату' : '',
        time: !formData.time ? 'Выберите время' : ''
      };

      let firstErrorRef = null;
      let firstErrorField = '';

      if (newErrors.phone) {
        firstErrorRef = phoneRef;
        firstErrorField = 'phone';
      } else if (newErrors.address) {
        firstErrorRef = addressRef;
        firstErrorField = 'address';
      } else if (newErrors.date) {
        firstErrorRef = dateRef;
        firstErrorField = 'date';
      } else if (newErrors.time) {
        firstErrorRef = timeRef;
        firstErrorField = 'time';
      }

      if (firstErrorRef?.current) {
        firstErrorRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setShakeField(firstErrorField);
        setTimeout(() => setShakeField(null), 600);
      }

      return;
    }

    const order = createOrder({
      ...formData,
      status: 'pending'
    });

    onClose();
    navigate('/orders', { state: { newOrderId: order.id } });
  };

  const totalPrice = cart.reduce((sum, item) => sum + calculateItemPrice(item), 0);
  const totalDiscount = cart.reduce((sum, item) => {
    const discount = getDiscount(item.quantity);
    const basePrice = item.selectedOption === 'install-only' ? item.product.priceInstallOnly : item.product.priceWithWiring;
    const fullPrice = basePrice * item.quantity;
    return sum + (fullPrice * discount / 100);
  }, 0);

  const wiringItems = cart.filter(item => item.selectedOption === 'full-wiring');
  const totalFrames = calculateFrames(wiringItems);
  const cableMeters = totalFrames * 8;
  
  const cableCost = cableMeters * 100;
  const finalTotal = totalPrice + cableCost;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader className="sr-only">
          <DialogTitle className="text-2xl font-bold">Запись к мастеру</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          <Card className="p-6">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="User" size={20} className="text-primary" />
              Контактные данные
            </h2>
            
            <div className="space-y-4">
              <div ref={phoneRef} className={shakeField === 'phone' ? 'shake-animation' : ''}>
                <label className="text-sm font-medium mb-2 block">
                  Номер телефона <span className="text-red-500">*</span>
                </label>
                <IMaskInput
                  mask="8 (000) 000-00-00"
                  value={formData.phone}
                  onAccept={(value: string) => setFormData({ ...formData, phone: value })}
                  placeholder="8 (___) ___-__-__"
                  className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    errors.phone ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.phone && (
                  <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                    <Icon name="AlertCircle" size={14} />
                    {errors.phone}
                  </p>
                )}
              </div>

              <div ref={addressRef} className={shakeField === 'address' ? 'shake-animation' : ''}>
                <label className="text-sm font-medium mb-2 block">
                  Адрес: (желательно)
                </label>
                <input
                  type="text"
                  placeholder="Улица, дом, квартира"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    errors.address ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.address && (
                  <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                    <Icon name="AlertCircle" size={14} />
                    {errors.address}
                  </p>
                )}
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-indigo-200 shadow-lg">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="Calendar" size={20} className="text-indigo-600" />
              <span className="text-indigo-900">Дата и время</span>
            </h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div ref={dateRef} className={shakeField === 'date' ? 'shake-animation' : ''}>
                <label className="text-sm font-medium mb-2 block text-gray-700">
                  Дата
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all bg-white shadow-sm ${
                    errors.date ? 'border-red-500' : 'border-indigo-300'
                  }`}
                />
                {errors.date && (
                  <p className="text-xs text-red-500 mt-1">{errors.date}</p>
                )}
              </div>
              <div ref={timeRef} className={shakeField === 'time' ? 'shake-animation' : ''}>
                <label className="text-sm font-medium mb-2 block text-gray-700">
                  Время
                </label>
                <select
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all bg-white shadow-sm ${
                    errors.time ? 'border-red-500' : 'border-indigo-300'
                  }`}
                >
                  <option value="">Выберите</option>
                  <option value="09:00">09:00</option>
                  <option value="10:00">10:00</option>
                  <option value="11:00">11:00</option>
                  <option value="12:00">12:00</option>
                  <option value="13:00">13:00</option>
                  <option value="14:00">14:00</option>
                  <option value="15:00">15:00</option>
                  <option value="16:00">16:00</option>
                  <option value="17:00">17:00</option>
                  <option value="18:00">18:00</option>
                </select>
                {errors.time && (
                  <p className="text-xs text-red-500 mt-1">{errors.time}</p>
                )}
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-green-800 font-medium mb-1">Стоимость работ</p>
                <div className="text-3xl font-bold text-green-900">{finalTotal.toLocaleString('ru-RU')} ₽</div>
              </div>
              <Icon name="BadgeCheck" size={48} className="text-green-600" />
            </div>
            {totalDiscount > 0 && (
              <div className="text-sm text-green-700 mb-2 font-medium">
                Ваша экономия: {totalDiscount.toLocaleString('ru-RU')} ₽
              </div>
            )}
            {cableMeters > 0 && (
              <>
                <div className="text-sm text-green-700 font-medium bg-green-100 p-3 rounded-lg">
                  Кабель: примерно {cableMeters} метров
                  <div className="text-xs text-green-600 mt-1">
                    Стоимость кабеля: ~{cableCost.toLocaleString('ru-RU')} ₽
                  </div>
                </div>
                <div className="text-sm text-green-700 font-medium bg-green-100 p-3 rounded-lg mt-2">
                  Кабель и расходный материал: ~{Math.round(cableMeters * 130).toLocaleString('ru-RU')} ₽
                  <div className="text-xs text-green-600 mt-1">
                    Из расчёта 130₽ на 1 погонный метр кабеля
                  </div>
                </div>
              </>
            )}
          </Card>

          <Card className="p-6 bg-blue-50 border-blue-200">
            <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
              <Icon name="HelpCircle" size={20} className="text-blue-600" />
              Что дальше?
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">1</div>
                <div>
                  <p className="font-semibold text-gray-800">Подтверждение заявки</p>
                  <p className="text-sm text-gray-600">Мастер свяжется с вами в течение часа</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">2</div>
                <div>
                  <p className="font-semibold text-gray-800">Встреча на объекте</p>
                  <p className="text-sm text-gray-600">Мастер приедет в указанное время либо для работы, либо осмотра фронта работ</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">3</div>
                <div>
                  <p className="font-semibold text-gray-800">Выполнение работ</p>
                  <p className="text-sm text-gray-600">Качественно и в срок</p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
            <div className="mb-3">
              <h3 className="font-bold text-lg">Бесплатная консультация</h3>
            </div>
            <p className="text-sm text-gray-700 mb-4">
              Есть вопросы? Напишите нам — мы с радостью проконсультируем вас!
            </p>
            <div className="flex gap-3">
              <a
                href="https://t.me/konigelectric"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white px-4 py-3 rounded-lg transition-all font-semibold shadow-md"
              >
                <Icon name="Send" size={18} />
                Welcome to Telegram 🚀
              </a>
              <Button
                variant="outline"
                className="flex-1"
                asChild
              >
                <a
                  href="https://vk.com/im?sel=-23524557"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2"
                >
                  <Icon name="MessageSquare" size={18} />
                  Написать во Вконтакте
                </a>
              </Button>
            </div>
          </Card>

          <Button
            size="lg"
            onClick={handleSubmit}
            className="w-full h-14 text-base font-semibold shadow-lg bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
          >
            <Icon name="CheckCircle" size={20} className="mr-2" />
            Оформить заявку
          </Button>
        </div>

        <style>{`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
            20%, 40%, 60%, 80% { transform: translateX(4px); }
          }
          .shake-animation {
            animation: shake 0.6s ease-in-out;
          }
        `}</style>
      </DialogContent>
    </Dialog>
  );
}