import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { IMaskInput } from 'react-imask';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { calculateItemPrice, getDiscount, getCableDiscount, calculateFrames } from '@/types/electrical';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import ContactModal from '@/components/ContactModal';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { cart, createOrder } = useCart();
  const [showContactModal, setShowContactModal] = useState(false);
  const phoneInputRef = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState({
    phone: '',
    address: '',
    date: '',
    time: ''
  });

  const [errors, setErrors] = useState({
    phone: ''
  });

  const totalPrice = cart.reduce((sum, item) => {
    if (item.product.id === 'auto-cable-wiring') return sum;
    return sum + calculateItemPrice(item);
  }, 0);
  
  const totalDiscount = cart.reduce((sum, item) => {
    if (item.product.id === 'auto-cable-wiring') return sum;
    if (item.product.discountApplied) return sum;
    const discount = getDiscount(item.quantity);
    const basePrice = item.selectedOption === 'install-only' ? item.product.priceInstallOnly : item.product.priceWithWiring;
    const fullPrice = basePrice * item.quantity;
    return sum + (fullPrice * discount / 100);
  }, 0);

  const cableWiringItem = cart.find(item => item.product.id === 'auto-cable-wiring');
  const cableMeters = cableWiringItem ? cableWiringItem.quantity : 0;
  const cableCost = cableWiringItem ? calculateItemPrice(cableWiringItem) : 0;
  
  const cableDiscount = cableMeters > 0 ? getCableDiscount(cableMeters) : 0;
  const baseCableCost = cableMeters * 100;
  const cableSavings = baseCableCost - cableCost;
  
  const wiringItems = cart.filter(item => 
    item.selectedOption === 'full-wiring' && item.product.id !== 'auto-cable-wiring'
  );
  
  const totalFrames = calculateFrames(wiringItems);
  
  const materialsCost = Math.round(cableMeters * 130);
  const finalTotal = totalPrice + cableCost;

  const validateForm = () => {
    const newErrors = { phone: '' };
    if (!formData.phone || formData.phone.replace(/[^0-9]/g, '').length < 11) {
      newErrors.phone = 'Укажите номер телефона';
      setErrors(newErrors);
      
      setTimeout(() => {
        phoneInputRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }, 100);
      
      return false;
    }
    setErrors(newErrors);
    return !newErrors.phone;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    const order = createOrder({
      ...formData,
      status: 'pending'
    });

    navigate('/thank-you', { state: { newOrderId: order.id } });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />

        <div className="p-6 space-y-4">
          <Card className="p-6 space-y-4">
            <div ref={phoneInputRef}>
              <label className="block text-sm font-semibold mb-2">
                Телефон <span className="text-red-500">*</span>
              </label>
              <IMaskInput
                mask="8 (000) 000-00-00"
                value={formData.phone}
                onAccept={(value: string) => setFormData({ ...formData, phone: value })}
                placeholder="8 (___) ___-__-__"
                className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                  errors.phone ? 'border-red-500 animate-shake' : 'border-gray-300'
                }`}
              />
              {errors.phone && (
                <p className="text-red-500 text-xs mt-1">{errors.phone}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">
                Адрес: (желательно)
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Калининград, ул. Пример, 1"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-2">
                  Дата
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">
                  Время
                </label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-blue-50 border-2 border-blue-200">
            <h3 className="font-bold text-base sm:text-lg mb-4 whitespace-nowrap overflow-hidden text-ellipsis">
              Стоимость работ в Калининграде
            </h3>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Работы без учёта кабеля:</span>
                <span className="font-bold">{totalPrice.toLocaleString('ru-RU')} ₽</span>
              </div>

              {cableMeters > 0 && (
                <>
                  <div className="flex justify-between text-sm">
                    <span>Монтаж кабеля (~{cableMeters} м):</span>
                    <span className="font-bold">{cableCost.toLocaleString('ru-RU')} ₽</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Кабель и расходный материал:</span>
                    <span className="font-semibold">{materialsCost.toLocaleString('ru-RU')} ₽</span>
                  </div>
                </>
              )}
              
              {totalFrames > 0 && (
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Необходимо рамок:</span>
                  <span className="font-semibold">{totalFrames} шт</span>
                </div>
              )}

              {(totalDiscount > 0 || cableSavings > 0) && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Общая экономия:</span>
                  <span className="font-bold">-{(totalDiscount + cableSavings).toLocaleString('ru-RU')} ₽</span>
                </div>
              )}

              <div className="border-t-2 border-dashed border-blue-300 pt-3 mt-3">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-bold">ИТОГО:</span>
                  <span className="text-2xl font-bold text-primary">{finalTotal.toLocaleString('ru-RU')} ₽</span>
                </div>
              </div>
            </div>
          </Card>

          <Button
            size="lg"
            onClick={handleSubmit}
            className="w-full h-14 text-base font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            Отправить заявку
          </Button>

          <Button
            variant="outline"
            onClick={() => navigate('/cart')}
            className="w-full"
          >
            Назад к плану
          </Button>
        </div>
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        .animate-shake {
          animation: shake 0.3s ease-in-out;
        }
      `}</style>
    </div>
  );
}