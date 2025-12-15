import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useReviews } from '@/contexts/ReviewContext';
import ElectricianRatingCard from '@/components/reviews/ElectricianRatingCard';
import ReviewList from '@/components/reviews/ReviewList';

const PORTFOLIO_ITEMS = [
  {
    id: '1',
    title: 'ЖК РЫБНАЯ ДЕРЕВНЯ: ОСТРОВ КАНТА',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '450 000 ₽',
    description: 'Комплексный электромонтаж новой проводки в просторной квартире в элитном ЖК на Острове Канта. Полный цикл работ от прокладки кабеля до установки розеток и выключателей. 9 фото.'
  },
  {
    id: '2',
    title: 'ЖК ВЫСОТА 56: Р-Н СЕЛЬМА',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '100 000 ₽',
    description: 'Монтаж новой электропроводки в квартире в ЖК Высота 56. Установка розеток, выключателей, прокладка кабельных трасс. Профессиональная работа с гарантией. 3 фото.'
  },
  {
    id: '3',
    title: 'Работа в новостройке',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '37 500 ₽',
    description: 'Интересный проект монтажа электрики в новой квартире. Установка подрозетников, прокладка кабеля, монтаж выключателей. Качественное выполнение в срок. 5 фото.'
  },
  {
    id: '4',
    title: 'Квартира в Московском районе, с учётом кабеля',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '52 000 ₽',
    description: 'Полный монтаж электропроводки в квартире в Московском районе. Стоимость включает все материалы: кабель, подрозетники, гофру. Работа под ключ. 4 фото.'
  },
  {
    id: '5',
    title: 'ЖК на Арсенальной - Калининград',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '150 000 ₽',
    description: 'Электромонтаж в современном ЖК на Арсенальной. Комплексные работы по монтажу электрики: от разводки в щитке до установки розеток и освещения. 3 фото.'
  },
  {
    id: '6',
    title: 'ЖК 3 Кита',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '38 000 ₽',
    description: 'Электромонтажные работы в квартире в ЖК 3 Кита. Установка розеток, выключателей, монтаж освещения. Аккуратная работа с соблюдением всех норм. 3 фото.'
  },
  {
    id: '7',
    title: 'ЖК «Гурьевский»',
    image: 'https://cdn.poehali.dev/files/7db6218d-3dca-4c32-bbfe-c06b61adda33.jpg',
    price: '34 500 ₽',
    description: 'Монтаж электропроводки в квартире в ЖК Гурьевский. Штробление, прокладка кабеля, установка электроточек. Профессиональный подход к каждой детали. 3 фото.'
  }
];

export default function Portfolio() {
  const navigate = useNavigate();
  const { getElectricianRating, reviews } = useReviews();
  const [selectedTab, setSelectedTab] = useState<'portfolio' | 'reviews'>('portfolio');
  
  const electricianRating = getElectricianRating('electrician-1');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 pb-24">
      <div className="max-w-md mx-auto">
        <div className="bg-white shadow-md p-6 space-y-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/electrical')}
            >
              <Icon name="ArrowLeft" size={24} />
            </Button>
            <h1 className="text-2xl font-bold flex-1">Портфолио и отзывы</h1>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {electricianRating && (
            <ElectricianRatingCard rating={electricianRating} />
          )}

          <div className="flex gap-2 bg-white rounded-lg p-1 shadow-sm">
            <Button
              variant={selectedTab === 'portfolio' ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setSelectedTab('portfolio')}
            >
              <Icon name="Image" size={18} className="mr-2" />
              Работы
            </Button>
            <Button
              variant={selectedTab === 'reviews' ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setSelectedTab('reviews')}
            >
              <Icon name="Star" size={18} className="mr-2" />
              Отзывы {reviews.length > 0 && `(${reviews.length})`}
            </Button>
          </div>

          {selectedTab === 'portfolio' && (
            <div className="space-y-4">
              {PORTFOLIO_ITEMS.map(item => (
                <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-all">
                  <div className="p-4">
                    <h3 className="font-bold text-base mb-2">{item.title}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{item.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-bold text-[#FF8C00]">{item.price}</span>
                      <Button size="sm" onClick={() => navigate('/calculator')}>
                        Заказать похожее
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {selectedTab === 'reviews' && (
            <div className="space-y-4">
              <div style={{ height: '800px', overflow: 'hidden', position: 'relative' }}>
                <iframe
                  title="Отзывы Яндекс Услуги"
                  style={{
                    width: '100%',
                    height: '100%',
                    border: '1px solid #e6e6e6',
                    borderRadius: '8px',
                    boxSizing: 'border-box'
                  }}
                  src="https://yandex.ru/maps-reviews-widget/159261695633?comments"
                />
                <a
                  href="https://yandex.ru/maps/org/uslugi_elektrika/159261695633/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    boxSizing: 'border-box',
                    textDecoration: 'none',
                    color: '#b3b3b3',
                    fontSize: '10px',
                    fontFamily: 'YS Text,sans-serif',
                    padding: '0 20px',
                    position: 'absolute',
                    bottom: '8px',
                    width: '100%',
                    textAlign: 'center',
                    left: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: 'block',
                    maxHeight: '14px',
                    whiteSpace: 'nowrap'
                  }}
                >
                  Услуги электрика на карте Калининграда — Яндекс&nbsp;Карты
                </a>
              </div>
              
              <div style={{ display: 'none' }}>
                <ReviewList reviews={reviews} showOrderId={true} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}