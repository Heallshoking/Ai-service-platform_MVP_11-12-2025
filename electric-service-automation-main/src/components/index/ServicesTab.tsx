import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { Service } from './types';

interface ServicesTabProps {
  servicesList: Service[];
  updateQuantity: (serviceId: string, change: number) => void;
}

export default function ServicesTab({ servicesList, updateQuantity }: ServicesTabProps) {
  return (
    <div className="space-y-6 animate-fade-in pb-24">
      <section className="space-y-4">
        <div className="text-center space-y-2">
          <h2 className="font-heading text-2xl md:text-3xl font-bold text-foreground">
            Услуги электрика
          </h2>
          <p className="text-muted-foreground text-sm">Выберите услугу и добавьте в заявку</p>
        </div>
        <div className="grid gap-3">
          {servicesList.map((service) => (
            <Card key={service.id} className="overflow-hidden bg-card border hover:shadow-md transition-all">
              <div className="flex items-stretch">
                <div className="w-20 flex-shrink-0 bg-primary/5 flex items-center justify-center">
                  <Icon name={service.icon as any} className="text-primary" size={32} />
                </div>
                <div className="flex-1 p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-base text-foreground">{service.title}</h3>
                      <p className="text-xs text-muted-foreground mt-1">{service.description}</p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="font-bold text-lg text-primary">{service.price} ₽</p>
                    </div>
                  </div>
                  {(service.quantity || 0) > 0 ? (
                    <div className="flex items-center gap-3 mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => updateQuantity(service.id, -1)}
                        className="h-9 w-9 p-0 rounded-full"
                      >
                        <Icon name="Minus" size={16} />
                      </Button>
                      <span className="font-bold text-lg min-w-[2rem] text-center">{service.quantity}</span>
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
                      className="w-full mt-3"
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
