import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import confetti from 'canvas-confetti';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { calculateItemPrice, getDiscount, calculateFrames } from '@/types/electrical';
import NewProgressBar from '@/components/NewProgressBar';
import ContactModal from '@/components/ContactModal';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import CheckoutContactForm from '@/components/checkout/CheckoutContactForm';
import CheckoutDateTimeForm from '@/components/checkout/CheckoutDateTimeForm';
import CheckoutCommentsForm from '@/components/checkout/CheckoutCommentsForm';
import CheckoutInfoCards from '@/components/checkout/CheckoutInfoCards';

export default function Checkout() {
  const navigate = useNavigate();
  const { cart, createOrder } = useCart();
  const { isAuthenticated } = useAuth();
  const [showContactModal, setShowContactModal] = useState(false);

  const [formData, setFormData] = useState({
    customerName: '',
    phone: '',
    address: '',
    date: '',
    time: '',
    comments: '',
    projectFiles: [] as File[]
  });

  const [errors, setErrors] = useState({
    customerName: '',
    phone: '',
    address: '',
    date: '',
    time: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors = {
      customerName: '',
      phone: '',
      address: '',
      date: '',
      time: ''
    };

    if (!formData.customerName) {
      newErrors.customerName = 'Укажите ваше имя';
    }

    if (!formData.phone) {
      newErrors.phone = 'Укажите номер телефона';
    } else if (!/^\+?[0-9]{10,15}$/.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Некорректный формат телефона';
    }

    if (!formData.address) {
      newErrors.address = 'Укажите адрес';
    }

    if (!formData.date) {
      newErrors.date = 'Выберите дату';
    }

    if (!formData.time) {
      newErrors.time = 'Выберите время';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some(err => err);
  };

  const fireConfetti = () => {
    const duration = 3000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 99999 };

    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const interval = window.setInterval(() => {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
      });
    }, 250);
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);

    const order = createOrder({
      ...formData,
      status: 'pending'
    });

    try {
      const emailHtml = `
        <h2>Новая заявка #${order.id.slice(0, 8)}</h2>
        <p><strong>Клиент:</strong> ${formData.customerName}</p>
        <p><strong>Телефон:</strong> ${formData.phone}</p>
        <p><strong>Адрес:</strong> ${formData.address}</p>
        <p><strong>Дата:</strong> ${formData.date}</p>
        <p><strong>Время:</strong> ${formData.time}</p>
        ${formData.comments ? `<p><strong>Комментарии:</strong> ${formData.comments}</p>` : ''}
        <p><strong>Сумма:</strong> ${finalTotal.toLocaleString('ru-RU')} ₽</p>
        <hr>
        <h3>Состав заказа:</h3>
        <ul>
          ${cart.map(item => `<li>${item.product.name} x ${item.quantity} - ${calculateItemPrice(item).toLocaleString('ru-RU')} ₽</li>`).join('')}
        </ul>
      `;
      
      await fetch('https://functions.poehali.dev/844c657d-c59c-4e46-a6dc-f58689204e01', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: 'electro.me@yandex.ru',
          subject: `NEW Заявка: ${formData.address}`,
          html: emailHtml
        })
      });
    } catch (error) {
      console.error('Ошибка отправки email:', error);
    }

    fireConfetti();
    
    setTimeout(() => {
      if (isAuthenticated) {
        navigate('/orders', { state: { newOrderId: order.id } });
      } else {
        navigate('/thank-you');
      }
    }, 1500);
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

  const steps = [
    { id: 1, label: 'Выберите услугу', icon: 'List' },
    { id: 2, label: 'План работ', icon: 'ClipboardList', onClick: () => navigate('/cart') },
    { id: 3, label: 'Оформление', icon: 'CheckCircle2' }
  ];

  if (cart.length === 0 && !isSubmitting) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <PageHeader />
        
        <div className="max-w-md mx-auto">
          <PageNavigation onContactClick={() => setShowContactModal(true)} />

          <div className="p-6">
            <Card className="p-12 text-center bg-white">
              <Icon name="ShoppingCart" size={64} className="text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Корзина пуста</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Добавьте услуги для оформления заявки
              </p>
              <Button
                onClick={() => navigate('/products')}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                Выбрать услуги
              </Button>
            </Card>
          </div>
        </div>

        <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-32">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />
        
        <div className="bg-white shadow-lg p-6 space-y-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/cart')}
            >
              <Icon name="ArrowLeft" size={24} />
            </Button>
            <h1 className="text-2xl font-bold text-gray-800 flex-1">Запись к мастеру</h1>
          </div>

          <NewProgressBar 
            steps={steps}
            currentStep={3}
            hasItems={true}
            cartConfirmed={true}
          />
        </div>

        <div className="p-6 space-y-6">
          <CheckoutContactForm
            formData={formData}
            errors={errors}
            onFormDataChange={(data) => setFormData({ ...formData, ...data })}
          />

          <CheckoutDateTimeForm
            formData={formData}
            errors={errors}
            onFormDataChange={(data) => setFormData({ ...formData, ...data })}
          />

          <CheckoutCommentsForm
            formData={formData}
            onFormDataChange={(data) => setFormData({ ...formData, ...data })}
          />

          <CheckoutInfoCards
            finalTotal={finalTotal}
            totalDiscount={totalDiscount}
            cableMeters={cableMeters}
            cableCost={cableCost}
          />

          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full h-14 text-base font-semibold shadow-lg bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Icon name="Loader2" size={20} className="mr-2 animate-spin" />
                Отправка...
              </>
            ) : (
              <>
                <Icon name="CheckCircle" size={20} className="mr-2" />
                Оформить заявку
              </>
            )}
          </Button>
        </div>
      </div>

      {isSubmitting && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="p-8 text-center bg-white max-w-sm mx-4">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <Icon name="Loader2" size={32} className="text-white animate-spin" />
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Отправка заявки...</h3>
            <p className="text-sm text-gray-600">Пожалуйста, подождите</p>
          </Card>
        </div>
      )}

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}
