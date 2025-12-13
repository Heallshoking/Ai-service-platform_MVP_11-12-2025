import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import { PortfolioItem } from '@/types/electrical';

const PORTFOLIO_ITEMS: PortfolioItem[] = [
  {
    id: '1',
    title: 'ЖК ВЫСОТА 56: Р-Н СЕЛЬМА',
    image: 'https://cdn.poehali.dev/files/dc78d8d9-0436-415f-ade9-9b1e7b215d6e.jpeg',
    price: '100 000 ₽',
    description: 'Полный электромонтаж квартиры'
  },
  {
    id: '2',
    title: 'Установить автомат',
    image: 'https://cdn.poehali.dev/files/dc78d8d9-0436-415f-ade9-9b1e7b215d6e.jpeg',
    price: '1 000 ₽',
    description: 'Установка автоматического выключателя'
  },
  {
    id: '3',
    title: 'Электромонтаж',
    image: 'https://cdn.poehali.dev/files/dc78d8d9-0436-415f-ade9-9b1e7b215d6e.jpeg',
    price: '35 000 ₽',
    description: 'Комплексные работы'
  }
];

export default function ElectricalHome() {
  const navigate = useNavigate();
  const { cart } = useCart();
  const [showVideoHint, setShowVideoHint] = useState(true);

  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="w-full pb-24">
        <img 
          src="https://cdn.poehali.dev/files/eef76e18-1b64-4ae3-8839-b4fe8da091be.jpg"
          alt="Калининград"
          className="w-full h-48 object-cover"
        />
        
        <div className="max-w-md mx-auto px-6 space-y-6 mt-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold">
              УСЛУГИ <span className="text-[#FF8C00]">ЭЛЕКТРИКА</span>
            </h1>
            <p className="text-sm text-muted-foreground">
              Рассчитайте стоимость работы за 2 минуты
            </p>
          </div>

          <Card 
            className="p-4 hover:shadow-md transition-all cursor-pointer border-2 hover:border-primary/50"
            onClick={() => navigate('/products')}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <Icon name="Wrench" size={24} className="text-[#FF8C00]" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-base">Выбрать услугу</h3>
                <p className="text-sm text-muted-foreground">Электромонтажные работы для квартиры</p>
              </div>
              <Icon name="ChevronRight" size={24} className="text-muted-foreground" />
            </div>
          </Card>

          <Button
            size="lg"
            className="w-full relative overflow-hidden bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white font-semibold h-16 text-base shadow-2xl rounded-2xl group"
            onClick={() => window.open('https://t.me/konigelectric', '_blank')}
          >
            <div className="flex items-center justify-center gap-3 relative z-10">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform">
                <Icon name="Send" size={20} className="text-white" />
              </div>
              <span className="text-lg">Написать в Telegram</span>
            </div>
          </Button>
        </div>
      </div>


    </div>
  );
}