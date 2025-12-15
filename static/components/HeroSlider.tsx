import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const slides = [
  {
    id: 1,
    icon: 'Lightbulb' as const,
    title: 'Управление освещением из 3-х мест',
    description: 'Включайте и выключайте свет из любой точки комнаты',
    color: 'from-amber-500 to-orange-600'
  },
  {
    id: 2,
    icon: 'Home' as const,
    title: 'Установка модулей умного дома',
    description: 'Автоматизация освещения, розеток и климата',
    color: 'from-blue-500 to-indigo-600'
  },
  {
    id: 3,
    icon: 'Lamp' as const,
    title: 'Подсветка кухонного гарнитура',
    description: 'LED-лента для рабочей зоны кухни',
    color: 'from-purple-500 to-pink-600'
  },
  {
    id: 4,
    icon: 'Plug' as const,
    title: 'Установка дополнительных розеток',
    description: 'Новые розетки в удобных местах без пыли',
    color: 'from-green-500 to-teal-600'
  },
  {
    id: 5,
    icon: 'ToggleLeft' as const,
    title: 'Перенос выключателя',
    description: 'Переместим выключатель в удобное место',
    color: 'from-red-500 to-rose-600'
  }
];

const HeroSlider = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="hidden md:block mb-12">
      <div className="relative h-64 overflow-hidden rounded-3xl">
        {slides.map((slide, index) => (
          <Card
            key={slide.id}
            className={`absolute inset-0 transition-all duration-700 ease-in-out ${
              index === currentSlide
                ? 'opacity-100 translate-x-0'
                : index < currentSlide
                ? 'opacity-0 -translate-x-full'
                : 'opacity-0 translate-x-full'
            } bg-gradient-to-r ${slide.color} border-0 text-white p-12 flex items-center justify-between`}
          >
            <div className="flex-1 space-y-4">
              <h2 className="font-heading text-4xl font-bold drop-shadow-lg">
                {slide.title}
              </h2>
              <p className="text-xl text-white/90 drop-shadow-md">
                {slide.description}
              </p>
            </div>
            <div className="w-32 h-32 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center ml-8">
              <Icon name={slide.icon} size={64} className="text-white drop-shadow-lg" />
            </div>
          </Card>
        ))}
      </div>

      <div className="flex justify-center gap-2 mt-6">
        {slides.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentSlide(index)}
            className={`h-2 rounded-full transition-all duration-300 ${
              index === currentSlide
                ? 'w-8 bg-primary'
                : 'w-2 bg-muted-foreground/30 hover:bg-muted-foreground/50'
            }`}
            aria-label={`Перейти к слайду ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default HeroSlider;
