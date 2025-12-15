import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Service } from '@/types/services';
import OrderProgressBar from '@/components/OrderProgressBar';
import { toast } from '@/hooks/use-toast';

const Tasks = () => {
  const navigate = useNavigate();
  const [cart, setCart] = useState<{ service: Service; quantity: number }[]>([]);

  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  }, []);

  const updateQuantity = (serviceId: string, newQuantity: number) => {
    const updated = cart.map(item => 
      item.service.id === serviceId ? { ...item, quantity: Math.max(0, newQuantity) } : item
    ).filter(item => item.quantity > 0);
    
    setCart(updated);
    localStorage.setItem('cart', JSON.stringify(updated));
  };

  const removeFromCart = (serviceId: string) => {
    const updated = cart.filter(item => item.service.id !== serviceId);
    setCart(updated);
    localStorage.setItem('cart', JSON.stringify(updated));
    toast({
      title: "Удалено",
      description: "Услуга удалена из списка"
    });
  };

  const getTotalPrice = () => {
    return cart.reduce((sum, item) => sum + (item.service.price * item.quantity), 0);
  };

  const getTotalItems = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const handleContinue = () => {
    if (cart.length === 0) {
      toast({
        title: "Список пуст",
        description: "Добавьте услуги для продолжения",
        variant: "destructive"
      });
      return;
    }
    navigate('/schedule');
  };

  return (
    <div className="min-h-screen bg-background pb-24">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <Button variant="ghost" onClick={() => navigate('/')} className="gap-2">
              <Icon name="ArrowLeft" size={20} />
              Назад
            </Button>
            <h1 className="font-heading font-bold text-lg">Список задач</h1>
            <Button variant="ghost" onClick={() => navigate('/order-history')} className="text-sm">
              История
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="bg-primary/5 rounded-lg p-4 border border-primary/20">
            <div className="flex items-start gap-3">
              <Icon name="Video" size={24} className="text-primary flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-1">Видео-инструкция за 2 минуты</h3>
                <Button variant="link" className="h-auto p-0 text-sm">
                  Посмотреть как это работает
                </Button>
              </div>
            </div>
          </div>

          <OrderProgressBar currentStatus="planning" />

          <Card className="p-1">
            <div className="bg-muted/50 p-4 rounded-t-lg border-b-2 border-dashed">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-bold text-lg">Выбранные услуги</h2>
                <Button variant="ghost" size="sm" onClick={() => navigate('/')} className="gap-2">
                  <Icon name="Plus" size={16} />
                  Добавить
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 rounded-full"
                  onClick={() => {
                    navigate('/');
                    setTimeout(() => {
                      const quickBtn = document.querySelector('[data-category="quick"]') as HTMLElement;
                      quickBtn?.click();
                    }, 100);
                  }}
                >
                  <Icon name="Zap" size={14} className="mr-1" />
                  Вызов электрика
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 rounded-full"
                  onClick={() => {
                    navigate('/');
                    setTimeout(() => {
                      const electricalBtn = document.querySelector('[data-category="electrical"]') as HTMLElement;
                      electricalBtn?.click();
                    }, 100);
                  }}
                >
                  <Icon name="Wrench" size={14} className="mr-1" />
                  Электромонтаж
                </Button>
              </div>
            </div>

            {cart.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground px-4">
                <Icon name="ShoppingCart" size={64} className="mx-auto mb-4 opacity-30" />
                <p className="text-lg mb-4">Список задач пуст</p>
                <Button onClick={() => navigate('/')} size="lg">
                  <Icon name="Plus" size={20} className="mr-2" />
                  Добавить услуги
                </Button>
              </div>
            ) : (
              <div className="p-4 space-y-3">
                {cart.map((item, index) => (
                  <div key={item.service.id} className="flex items-start gap-3 pb-3 border-b last:border-0">
                    <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-base">{item.service.name}</h3>
                      <p className="text-sm text-muted-foreground line-clamp-1">{item.service.description}</p>
                      
                      <div className="flex items-center gap-4 mt-3">
                        <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8"
                            onClick={() => updateQuantity(item.service.id, item.quantity - 1)}
                          >
                            <Icon name="Minus" size={16} />
                          </Button>
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) => {
                              const val = parseInt(e.target.value) || 1;
                              updateQuantity(item.service.id, val);
                            }}
                            className="w-12 text-center font-bold bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-primary rounded"
                          />
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8"
                            onClick={() => updateQuantity(item.service.id, item.quantity + 1)}
                          >
                            <Icon name="Plus" size={16} />
                          </Button>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">{item.service.price.toLocaleString()} ₽</span>
                          <span className="text-sm">×</span>
                          <span className="text-sm">{item.quantity}</span>
                          <span className="text-sm">=</span>
                          <span className="font-bold text-lg">
                            {(item.service.price * item.quantity).toLocaleString()} ₽
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => removeFromCart(item.service.id)}
                    >
                      <Icon name="X" size={18} />
                    </Button>
                  </div>
                ))}

                <div className="pt-4 mt-4 border-t-2 border-dashed">
                  <div className="flex items-center justify-between text-lg">
                    <span className="font-semibold">Итого:</span>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground mb-1">
                        {getTotalItems()} {getTotalItems() === 1 ? 'услуга' : 'услуг'}
                      </div>
                      <div className="font-bold text-2xl text-primary">
                        {getTotalPrice().toLocaleString()} ₽
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Card>

          <Card className="p-6 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-950 dark:to-amber-900 border-amber-200">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-amber-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="Info" size={24} className="text-amber-700 dark:text-amber-300" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-2 text-amber-900 dark:text-amber-100">Важно знать</h3>
                <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-1">
                  <li>• Итоговая цена может измениться после осмотра объекта</li>
                  <li>• Мастер свяжется с вами в течение 15-30 минут</li>
                  <li>• Выезд мастера на осмотр — бесплатно</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </main>

      {cart.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border shadow-lg z-50">
          <div className="container mx-auto px-4 py-4">
            <Button 
              size="lg" 
              className="w-full h-14 text-lg font-semibold shadow-lg gap-2"
              onClick={handleContinue}
            >
              Оформить заявку
              <Icon name="ArrowRight" size={22} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;