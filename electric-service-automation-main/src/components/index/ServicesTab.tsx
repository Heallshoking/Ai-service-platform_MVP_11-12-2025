import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { Service } from './types';
import CategorySection from './CategorySection';

interface ServicesTabProps {
  servicesList: Service[];
  updateQuantity: (serviceId: string, change: number) => void;
}

export default function ServicesTab({ servicesList, updateQuantity }: ServicesTabProps) {
  return (
    <div className="space-y-4 animate-fade-in pb-24">
      <CategorySection />
      
      <section className="space-y-3">
        <div className="text-center space-y-1">
          <h2 className="font-heading text-xl md:text-2xl font-bold text-foreground">
            Услуги электрика
          </h2>
          <p className="text-muted-foreground text-xs">Выберите услугу и добавьте в заявку</p>
        </div>
        <div className="grid gap-2">
          {servicesList.map((service) => (
            <Card key={service.id} className="overflow-hidden bg-card border hover:shadow-md transition-all">
              <div className="flex items-stretch">
                <div className="w-16 flex-shrink-0 bg-primary/5 flex items-center justify-center">
                  <Icon name={service.icon as any} className="text-primary" size={26} />
                </div>
                <div className="flex-1 p-3">
                  <div className="flex justify-between items-start mb-1.5">
                    <div className="flex-1">
                      <h3 className="font-semibold text-sm text-foreground">{service.title}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">{service.description}</p>
                    </div>
                    <div className="text-right ml-3">
                      <p className="font-bold text-base text-primary">{service.price} ₽</p>
                    </div>
                  </div>
                  {(service.quantity || 0) > 0 ? (
                    <div className="flex items-center gap-2.5 mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => updateQuantity(service.id, -1)}
                        className="h-9 w-9 p-0 rounded-full"
                      >
                        <Icon name="Minus" size={16} />
                      </Button>
                      <span className="font-bold text-base min-w-[2rem] text-center">{service.quantity}</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => updateQuantity(service.id, 1)}
                        className="h-9 w-9 p-0 rounded-full"
                      >
                        <Icon name="Plus" size={16} />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => updateQuantity(service.id, 1)}
                      className="w-full mt-2 h-8 text-xs"
                    >
                      Добавить
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
