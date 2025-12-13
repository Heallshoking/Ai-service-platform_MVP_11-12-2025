import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import ContactModal from '@/components/ContactModal';
import { IMaskInput } from 'react-imask';

export default function Profile() {
  const navigate = useNavigate();
  const { orders } = useCart();
  const { user, updateUser } = useAuth();
  const [showContactModal, setShowContactModal] = useState(false);
  const [isEditingPhone, setIsEditingPhone] = useState(false);
  const [phoneValue, setPhoneValue] = useState(user?.phone || '');

  useEffect(() => {
    if (user && user.role !== 'client') {
      navigate('/');
    }
  }, [user, navigate]);

  const handlePhoneSave = () => {
    if (phoneValue && phoneValue.replace(/\D/g, '').length === 11) {
      updateUser({ phone: phoneValue });
      setIsEditingPhone(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <img 
        src="https://cdn.poehali.dev/files/eef76e18-1b64-4ae3-8839-b4fe8da091be.jpg"
        alt="Калининград"
        className="w-full h-48 object-cover"
      />

      <div className="max-w-md mx-auto">
        <div className="bg-white shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/')}
              >
                <Icon name="ArrowLeft" size={24} />
              </Button>
              <h1 className="text-2xl font-bold text-gray-800 flex-1">Личный кабинет</h1>
            </div>
            <Button
              onClick={() => setShowContactModal(true)}
              className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 hover:from-blue-600 hover:via-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 p-0 hover:scale-110"
              title="Меню связи"
            >
              <Icon name="Menu" size={24} />
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <Card className="p-6 animate-fadeIn">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg">
                <Icon name="User" size={36} className="text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-800">Добро пожаловать!</h2>
                <p className="text-sm text-muted-foreground">Клиент сервиса</p>
                {user?.phone && (
                  <div className="mt-2">
                    {!isEditingPhone ? (
                      <button
                        onClick={() => {
                          setIsEditingPhone(true);
                          setPhoneValue(user.phone || '');
                        }}
                        className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                      >
                        <Icon name="Phone" size={14} />
                        {user.phone}
                        <Icon name="Edit2" size={12} />
                      </button>
                    ) : (
                      <div className="flex items-center gap-2 mt-2">
                        <IMaskInput
                          mask="8 (000) 000-00-00"
                          value={phoneValue}
                          onAccept={(value: string) => setPhoneValue(value)}
                          placeholder="8 (___) ___-__-__"
                          className="text-xs p-2 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-40"
                        />
                        <Button size="sm" onClick={handlePhoneSave} className="h-8">
                          <Icon name="Check" size={14} />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setIsEditingPhone(false)} className="h-8">
                          <Icon name="X" size={14} />
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full justify-start h-16 border-2 hover:border-blue-400 hover:bg-blue-50 transition-all hidden"
                onClick={() => navigate('/orders')}
              >
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-full flex items-center justify-center mr-4">
                  <Icon name="ShoppingBag" size={24} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-bold text-lg">Мои заявки</div>
                  <div className="text-xs text-muted-foreground">История и статусы заказов</div>
                </div>
                {orders.length > 0 && (
                  <span className="bg-primary text-white font-bold px-3 py-1 rounded-full text-sm">
                    {orders.length}
                  </span>
                )}
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start h-16 border-2 hover:border-green-400 hover:bg-green-50 transition-all"
                onClick={() => navigate('/')}
              >
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mr-4">
                  <Icon name="Plus" size={24} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-bold text-lg">Новая заявка</div>
                  <div className="text-xs text-muted-foreground">Заказать услуги электрика</div>
                </div>
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start h-16 border-2 hover:border-purple-400 hover:bg-purple-50 transition-all"
                onClick={() => navigate('/portfolio')}
              >
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center mr-4">
                  <Icon name="ImageIcon" size={24} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-bold text-lg">Портфолио</div>
                  <div className="text-xs text-muted-foreground">Наши выполненные работы</div>
                </div>
              </Button>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 animate-fadeIn">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Icon name="Phone" size={24} className="text-blue-600" />
              Контакты
            </h3>
            <div className="space-y-3">
              <a
                href="tel:+74012520725"
                className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-all"
              >
                <Icon name="Phone" size={20} className="text-green-600" />
                <div>
                  <p className="font-semibold text-gray-800">Позвонить</p>
                  <p className="text-sm text-gray-600">+7 (4012) 52-07-25</p>
                </div>
              </a>
              <a
                href="https://t.me/konigelectric"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-all"
              >
                <Icon name="Send" size={20} className="text-blue-600" />
                <div>
                  <p className="font-semibold text-gray-800">Telegram</p>
                  <p className="text-sm text-gray-600">@konigelectric</p>
                </div>
              </a>
              <a
                href="https://vk.com/im?sel=-23524557"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-all"
              >
                <Icon name="MessageCircle" size={20} className="text-blue-700" />
                <div>
                  <p className="font-semibold text-gray-800">ВКонтакте</p>
                  <p className="text-sm text-gray-600">Бесплатная консультация</p>
                </div>
              </a>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 animate-fadeIn">
            <div className="flex items-start gap-3">
              <Icon name="Info" size={24} className="text-amber-600 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-2 text-gray-800">О нас</h3>
                <p className="text-sm text-gray-700 mb-3">
                  ООО "Кёниг Электрик" — профессиональные электромонтажные работы в Калининграде и области
                </p>
                <div className="flex items-center gap-3 mb-3">
                  <a
                    href="https://t.me/konigelectric"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-600 transition-colors"
                    title="Telegram"
                  >
                    <Icon name="Send" size={20} />
                  </a>
                  <a
                    href="https://vk.com/im?sel=-23524557"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 transition-colors"
                    title="ВКонтакте"
                  >
                    <Icon name="MessageCircle" size={20} />
                  </a>
                  <a
                    href="tel:+74012520725"
                    className="text-green-600 hover:text-green-700 transition-colors"
                    title="Позвонить"
                  >
                    <Icon name="Phone" size={20} />
                  </a>
                </div>
                <p className="text-sm text-gray-700">
                  ⏰ Работаем: Пн-Вс, 8:00 - 20:00
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

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