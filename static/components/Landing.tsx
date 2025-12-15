import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

export default function Landing() {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    element?.scrollIntoView({ behavior: 'smooth' });
    setIsMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-white">
      <header className="fixed top-0 left-0 right-0 bg-white shadow-sm z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-2">
              <Icon name="Zap" size={32} className="text-orange-500" />
              <span className="text-xl font-bold text-gray-900">Балтсеть | Услуги электрика ³⁹</span>
            </div>
            
            <nav className="hidden md:flex items-center gap-8">
              <button onClick={() => scrollToSection('services')} className="text-gray-700 hover:text-orange-500 transition-colors">Услуги</button>
              <button onClick={() => scrollToSection('about')} className="text-gray-700 hover:text-orange-500 transition-colors">О нас</button>
              <button onClick={() => scrollToSection('advantages')} className="text-gray-700 hover:text-orange-500 transition-colors">Преимущества</button>
              <button onClick={() => scrollToSection('contacts')} className="text-gray-700 hover:text-orange-500 transition-colors">Контакты</button>
              <Button onClick={() => navigate('/products')} className="bg-orange-500 hover:bg-orange-600">
                Заказать услугу
              </Button>
            </nav>

            <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden">
              <Icon name={isMenuOpen ? 'X' : 'Menu'} size={24} />
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <div className="md:hidden border-t bg-white">
            <div className="px-4 py-2 space-y-2">
              <button onClick={() => scrollToSection('services')} className="block w-full text-left py-2 text-gray-700">Услуги</button>
              <button onClick={() => scrollToSection('about')} className="block w-full text-left py-2 text-gray-700">О нас</button>
              <button onClick={() => scrollToSection('advantages')} className="block w-full text-left py-2 text-gray-700">Преимущества</button>
              <button onClick={() => scrollToSection('contacts')} className="block w-full text-left py-2 text-gray-700">Контакты</button>
              <Button onClick={() => navigate('/products')} className="w-full bg-orange-500 hover:bg-orange-600">
                Заказать услугу
              </Button>
            </div>
          </div>
        )}
      </header>

      <section className="pt-32 pb-20 bg-gradient-to-br from-orange-50 to-yellow-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                Электромонтажные работы в&nbsp;Калининграде
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Профессиональные услуги электрика для квартир, домов и коммерческих объектов. Быстро, качественно, с гарантией.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button onClick={() => navigate('/products')} size="lg" className="bg-orange-500 hover:bg-orange-600 text-lg px-8 py-6">
                  Рассчитать стоимость
                </Button>
                <Button onClick={() => scrollToSection('contacts')} variant="outline" size="lg" className="text-lg px-8 py-6">
                  Связаться с нами
                </Button>
              </div>
            </div>
            <div className="hidden md:flex items-center justify-center">
              <div className="relative w-full h-96 rounded-3xl overflow-hidden shadow-2xl">
                <img 
                  src="https://cdn.poehali.dev/files/612d720b-8d12-4203-80db-20bcf3522f82.jpg" 
                  alt="Калининград" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="services" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">Услуги электрика</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: 'Lightbulb', title: 'Установка светильников', desc: 'Монтаж люстр, бра, светильников любой сложности' },
              { icon: 'Plug', title: 'Розетки и выключатели', desc: 'Установка, замена, перенос розеток и выключателей' },
              { icon: 'Cpu', title: 'Электрощиты', desc: 'Монтаж и сборка электрощитов, установка автоматов' },
              { icon: 'Cable', title: 'Замена проводки', desc: 'Полная или частичная замена электропроводки' },
              { icon: 'AlertCircle', title: 'Ремонт электрики', desc: 'Диагностика и устранение неисправностей' },
              { icon: 'Zap', title: 'Монтаж кабеля', desc: 'Прокладка кабеля в штробах и гофре' },
            ].map((service, i) => (
              <div key={i} className="p-6 border rounded-2xl hover:shadow-xl transition-all cursor-pointer group">
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-orange-500 transition-colors">
                  <Icon name={service.icon as any} size={32} className="text-orange-500 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl font-bold mb-2">{service.title}</h3>
                <p className="text-gray-600">{service.desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-12">
            <Button onClick={() => navigate('/products')} size="lg" className="bg-orange-500 hover:bg-orange-600">
              Посмотреть все услуги
            </Button>
          </div>
        </div>
      </section>

      <section id="about" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">О компании БАЛТСЕТЬ</h2>
              <p className="text-lg text-gray-600 mb-4">
                Мы — команда профессиональных электриков с многолетним опытом работы в Калининграде и области.
              </p>
              <p className="text-lg text-gray-600 mb-4">
                Выполняем электромонтажные работы любой сложности: от замены розетки до полной замены проводки в квартире или доме.
              </p>
              <p className="text-lg text-gray-600">
                Гарантируем качество, соблюдение сроков и прозрачное ценообразование.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-6">
              {[
                { num: '500+', text: 'Выполненных работ' },
                { num: '100%', text: 'Довольных клиентов' },
                { num: '10+', text: 'Лет опыта' },
                { num: '24/7', text: 'Поддержка' },
              ].map((stat, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl text-center shadow-md">
                  <div className="text-4xl font-bold text-orange-500 mb-2">{stat.num}</div>
                  <div className="text-gray-600">{stat.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="advantages" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">Почему выбирают нас</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { icon: 'CheckCircle', title: 'Гарантия качества', desc: 'Гарантия на все виды работ' },
              { icon: 'Clock', title: 'Точно в срок', desc: 'Соблюдаем оговоренные сроки' },
              { icon: 'DollarSign', title: 'Прозрачные цены', desc: 'Без скрытых доплат' },
              { icon: 'Users', title: 'Опытные мастера', desc: 'Профессионалы своего дела' },
            ].map((adv, i) => (
              <div key={i} className="text-center">
                <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Icon name={adv.icon as any} size={40} className="text-orange-500" />
                </div>
                <h3 className="text-xl font-bold mb-2">{adv.title}</h3>
                <p className="text-gray-600">{adv.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="contacts" className="py-20 bg-gradient-to-br from-orange-500 to-yellow-500 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-6">Готовы начать работу?</h2>
          <p className="text-xl mb-8">Свяжитесь с нами любым удобным способом</p>
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <a href="tel:+74012520725" className="bg-white text-gray-900 p-6 rounded-2xl hover:shadow-xl transition-all">
              <Icon name="Phone" size={32} className="mx-auto mb-3 text-orange-500" />
              <div className="font-bold">+7 (4012) 52-07-25</div>
            </a>
            <a href="https://t.me/konigelectric" target="_blank" rel="noopener noreferrer" className="bg-white text-gray-900 p-6 rounded-2xl hover:shadow-xl transition-all">
              <Icon name="Send" size={32} className="mx-auto mb-3 text-orange-500" />
              <div className="font-bold">Telegram</div>
            </a>
            <div className="bg-white text-gray-900 p-6 rounded-2xl">
              <Icon name="MapPin" size={32} className="mx-auto mb-3 text-orange-500" />
              <div className="font-bold">Калининград</div>
            </div>
          </div>
          <Button onClick={() => navigate('/products')} size="lg" variant="outline" className="bg-white text-orange-500 hover:bg-gray-100 border-0 text-lg px-8 py-6">
            Заказать услугу прямо сейчас
          </Button>
        </div>
      </section>

      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">© 2024 БАЛТСЕТЬ. Все права защищены.</p>
          <p className="text-gray-500 text-sm mt-2">Электромонтажные работы в Калининграде</p>
        </div>
      </footer>
    </div>
  );
}