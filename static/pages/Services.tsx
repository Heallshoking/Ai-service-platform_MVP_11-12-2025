import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import ContactModal from '@/components/ContactModal';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import Landing from '@/components/Landing';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';

export default function Services() {
  const navigate = useNavigate();
  const { cart } = useCart();
  const { user } = useAuth();
  const [showContactModal, setShowContactModal] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const hasItems = cart.length > 0;
  const isElectrician = user?.role === 'electrician';

  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(window.innerWidth >= 768);
    };
    
    checkDesktop();
    window.addEventListener('resize', checkDesktop);
    
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  if (isDesktop) {
    return <Landing />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <PageHeader />
      
      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />

        <div className="p-6 space-y-6">

        {hasItems && !isElectrician && (
          <Card className="p-6 bg-gradient-to-r from-blue-500 to-indigo-600 shadow-lg hover:shadow-xl transition-all cursor-pointer" onClick={() => navigate('/cart')}>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="PlayCircle" size={32} className="text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-1">Продолжить</h2>
                <p className="text-sm text-blue-100">Список задач ({cart.length})</p>
              </div>
            </div>
          </Card>
        )}

        {isElectrician ? (
          <Card className="p-6 bg-gradient-to-r from-blue-500 to-indigo-600 shadow-lg hover:shadow-xl transition-all cursor-pointer" onClick={() => navigate('/executor-profile-settings')}>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="User" size={32} className="text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-1">Профиль</h2>
                <p className="text-sm text-blue-100">Настройки и статистика</p>
              </div>
            </div>
          </Card>
        ) : null}
        
        <Card className="p-6 bg-white shadow-lg hover:shadow-xl transition-all cursor-pointer hidden" onClick={() => navigate('/orders')}>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
              <Icon name="Mail" size={32} className="text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-800 mb-1">{isElectrician ? 'Мои заказы' : 'Мои заявки'}</h2>
              <p className="text-sm text-gray-600">{isElectrician ? 'Назначенные мне работы' : 'История и статусы'}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white shadow-lg hover:shadow-xl transition-all cursor-pointer" onClick={() => navigate('/products')}>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <Icon name="Plus" size={32} className="text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-800 mb-1">Новая заявка</h2>
              <p className="text-sm text-gray-600">Услуги электрика</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white shadow-lg hover:shadow-xl transition-all cursor-pointer" onClick={() => navigate('/portfolio')}>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <Icon name="Image" size={32} className="text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-800 mb-1">Портфолио</h2>
              <p className="text-sm text-gray-600">Наши выполненные работы</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-blue-50 border border-blue-200">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Icon name="Phone" size={20} className="text-blue-600" />
            Контакты
          </h3>

          <div className="space-y-3">
            <a href="tel:+74012520725" className="flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors">
              <Icon name="Phone" size={20} className="text-green-600" />
              <div>
                <p className="text-sm text-gray-500">Позвонить</p>
                <p className="font-semibold">+7 (4012) 52-07-25</p>
              </div>
            </a>

            <a href="https://t.me/konigelectric" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors">
              <Icon name="Send" size={20} className="text-blue-600" />
              <div>
                <p className="text-sm text-gray-500">Telegram</p>
                <p className="font-semibold">@konigelectric</p>
              </div>
            </a>

            <a href="https://vk.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors">
              <Icon name="MessageCircle" size={20} className="text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">ВКонтакте</p>
                <p className="font-semibold">Задать вопрос</p>
              </div>
            </a>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200">
          <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
            <Icon name="Info" size={20} className="text-orange-600" />
            О нас
          </h3>
          <p className="text-sm text-gray-700 mb-3">
            БАЛТСЕТЬ <sup className="text-xs text-primary">³⁹</sup> — профессиональные электромонтажные работы в Калининграде и области
          </p>
          <p className="text-sm text-gray-600 flex items-center gap-2 mb-4">
            <Icon name="Clock" size={16} className="text-orange-600" />
            Работаем: Пн-Вс, 10:00 - 18:00
          </p>
          
          <div className="flex items-center gap-3 pt-3 border-t border-amber-200">
            <a
              href="https://t.me/konigelectric"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center p-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all hover:scale-105"
              title="Telegram"
            >
              <Icon name="Send" size={20} />
            </a>
            
            <a
              href="https://vk.com/im?sel=-23524557"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center p-3 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all hover:scale-105"
              title="ВКонтакте"
            >
              <Icon name="MessageCircle" size={20} />
            </a>
            
            <a
              href="tel:+74012520725"
              className="flex-1 flex items-center justify-center p-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all hover:scale-105"
              title="Позвонить"
            >
              <Icon name="Phone" size={20} />
            </a>
          </div>
        </Card>
        </div>
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
    </div>
  );
}