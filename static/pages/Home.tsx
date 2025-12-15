import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { quickServices, electricalServices, Service } from '@/types/services';
import ServiceCard from '@/components/ServiceCard';
import { useNavigate } from 'react-router-dom';
import { toast } from '@/hooks/use-toast';
import HeroSlider from '@/components/HeroSlider';

const Home = () => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<'quick' | 'electrical' | null>(null);
  const [cart, setCart] = useState<{ service: Service; quantity: number }[]>([]);

  const addToCart = (service: Service, quantity: number) => {
    setCart(prev => {
      const existing = prev.find(item => item.service.id === service.id);
      if (existing) {
        return prev.map(item => 
          item.service.id === service.id 
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { service, quantity }];
    });
  };

  const getTotalPrice = () => {
    return cart.reduce((sum, item) => sum + (item.service.price * item.quantity), 0);
  };

  const getTotalItems = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const handleGoToTasks = () => {
    localStorage.setItem('cart', JSON.stringify(cart));
    navigate('/tasks');
  };

  const handleBookInspection = () => {
    const inspectionService = quickServices.find(s => s.id === 'q3');
    if (inspectionService) {
      const updatedCart = [...cart];
      const existing = updatedCart.find(item => item.service.id === inspectionService.id);
      if (existing) {
        existing.quantity += 1;
      } else {
        updatedCart.push({ service: inspectionService, quantity: 1 });
      }
      setCart(updatedCart);
      localStorage.setItem('cart', JSON.stringify(updatedCart));
      toast({
        title: "Добавлено в список",
        description: "Вызов мастера на осмотр добавлен"
      });
      setTimeout(() => {
        navigate('/tasks');
      }, 800);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-amber-50 dark:from-slate-950 dark:via-blue-950 dark:to-amber-950 pb-24">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center gap-2">
              <Icon name="Zap" className="text-primary" size={24} />
              <div>
                <h1 className="font-heading font-bold text-lg text-foreground">БАЛТСЕТЬ <sup className="text-xs text-primary">³⁹</sup></h1>
                <p className="text-[10px] text-muted-foreground uppercase">Калининград</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-muted-foreground hover:text-primary text-xs"
                onClick={() => toast({ title: "Идея принята", description: "Спасибо за ваше участие в развитии сервиса!" })}
              >
                <Icon name="Lightbulb" size={16} />
                <span className="hidden sm:inline">Идея</span>
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                className="relative"
                onClick={handleGoToTasks}
              >
                <Icon name="ShoppingCart" size={24} />
                {getTotalItems() > 0 && (
                  <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {getTotalItems()}
                  </span>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {!selectedCategory ? (
          <div className="max-w-2xl mx-auto space-y-6">
            <HeroSlider />
            
            <div className="text-center space-y-3 mb-8 md:hidden">
              <h2 className="font-heading text-3xl font-bold text-foreground">
                Выберите категорию
              </h2>
              <p className="text-muted-foreground text-lg">Нажмите на карточку для продолжения</p>
              <div className="flex justify-center">
                <Icon name="ArrowDown" size={32} className="text-primary animate-bounce" />
              </div>
            </div>

            <div className="space-y-4">
              <Card 
                className="p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 hover:border-primary hover:scale-105 group active:scale-95"
                onClick={() => setSelectedCategory('quick')}
                data-category="quick"
              >
                <div className="flex items-center gap-6">
                  <div className="w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                    <Icon name="Zap" size={40} className="text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-2xl mb-2 group-hover:text-primary transition-colors">Вызов электрика на час</h3>
                    <p className="text-muted-foreground">Быстрая помощь для простых задач</p>
                  </div>
                  <Icon name="ChevronRight" size={28} className="text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Card>

              <Card 
                className="p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 hover:border-primary hover:scale-105 group active:scale-95"
                onClick={() => setSelectedCategory('electrical')}
                data-category="electrical"
              >
                <div className="flex items-center gap-6">
                  <div className="w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                    <Icon name="Wrench" size={40} className="text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-2xl mb-2 group-hover:text-primary transition-colors">Электромонтажные работы</h3>
                    <p className="text-muted-foreground">Комплексные работы и монтаж</p>
                  </div>
                  <Icon name="ChevronRight" size={28} className="text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Card>
            </div>

            <div className="mt-8">
              <Button 
                size="lg" 
                variant="outline"
                className="w-full h-16 text-lg font-semibold border-2 border-primary/30 hover:bg-primary/5 gap-3"
                onClick={handleBookInspection}
              >
                <Icon name="Calendar" size={24} className="text-primary" />
                Записаться на бесплатный осмотр
                <Icon name="ArrowRight" size={20} />
              </Button>
            </div>


          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                onClick={() => setSelectedCategory(null)}
                className="gap-2"
              >
                <Icon name="ArrowLeft" size={20} />
                Назад
              </Button>
            </div>

            <div className="text-center space-y-2">
              <h2 className="font-heading text-2xl md:text-3xl font-bold text-foreground">
                {selectedCategory === 'quick' ? 'Вызов электрика на час' : 'Электромонтажные работы'}
              </h2>
              <p className="text-muted-foreground">Выберите услуги и добавьте в список задач</p>
            </div>

            <div className={selectedCategory === 'quick' ? 'space-y-3' : 'grid md:grid-cols-2 lg:grid-cols-3 gap-4'}>
              {(selectedCategory === 'quick' ? quickServices : electricalServices).map(service => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  onAddToCart={(quantity) => addToCart(service, quantity)}
                  layout={selectedCategory === 'quick' ? 'list' : 'grid'}
                />
              ))}
            </div>

            {selectedCategory === 'quick' && (
              <div className="mt-12 space-y-8 max-w-4xl mx-auto">
                <div className="space-y-4">
                  <h3 className="font-bold text-2xl text-center">Отзывы наших клиентов</h3>
                  <div style={{height:'800px', overflow:'hidden', position:'relative'}}>
                    <iframe 
                      title="Яндекс Отзывы" 
                      style={{width:'100%', height:'100%', border:'1px solid #e6e6e6', borderRadius:'8px', boxSizing:'border-box'}} 
                      src="https://yandex.ru/maps-reviews-widget/159261695633?comments"
                    />
                    <a 
                      href="https://yandex.ru/maps/org/uslugi_elektrika/159261695633/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        boxSizing:'border-box',
                        textDecoration:'none',
                        color:'#b3b3b3',
                        fontSize:'10px',
                        fontFamily:'YS Text,sans-serif',
                        padding:'0 20px',
                        position:'absolute',
                        bottom:'8px',
                        width:'100%',
                        textAlign:'center',
                        left:0,
                        overflow:'hidden',
                        textOverflow:'ellipsis',
                        display:'block',
                        maxHeight:'14px',
                        whiteSpace:'nowrap'
                      }}
                    >
                      Услуги электрика на карте Калининграда — Яндекс&nbsp;Карты
                    </a>
                  </div>
                </div>
              </div>
            )}


          </div>
        )}
      </main>

      {getTotalItems() > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border shadow-lg z-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">
                  {getTotalItems()} {getTotalItems() === 1 ? 'услуга' : 'услуг'}
                </span>
                <span className="font-bold text-xl">{getTotalPrice().toLocaleString()} ₽</span>
              </div>
              <Button 
                size="lg" 
                className="gap-2 flex-1 max-w-xs h-14 text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
                onClick={handleGoToTasks}
              >
                Список задач
                <Icon name="ArrowRight" size={20} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;