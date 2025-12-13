import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import Icon from './ui/icon';
import { useState } from 'react';
import { Service } from '@/types/services';
import { toast } from '@/hooks/use-toast';

interface ServiceCardProps {
  service: Service;
  onAddToCart: (quantity: number) => void;
  layout?: 'grid' | 'list';
}

const ServiceCard = ({ service, onAddToCart, layout = 'grid' }: ServiceCardProps) => {
  const [quantity, setQuantity] = useState(1);

  const handleAdd = () => {
    onAddToCart(quantity);
    toast({
      title: "Добавлено в список",
      description: `${service.name} × ${quantity}`
    });
    setQuantity(1);
  };

  if (layout === 'list') {
    return (
      <Card className="overflow-hidden hover:shadow-md transition-all border-2 hover:border-primary/50">
        <div className="p-4">
          <div className="flex items-start gap-4">
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-lg mb-1">{service.name}</h3>
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{service.description}</p>
              
              <div className="flex items-center gap-2 mb-3">
                {service.oldPrice && (
                  <>
                    <span className="text-sm text-muted-foreground line-through">
                      {service.oldPrice.toLocaleString()} ₽
                    </span>
                    {service.discount && (
                      <Badge variant="destructive" className="text-xs">
                        -{service.discount}%
                      </Badge>
                    )}
                  </>
                )}
              </div>
              <span className="text-2xl font-bold text-primary">
                {service.price.toLocaleString()} ₽
              </span>
            </div>

            <div className="flex flex-col items-end gap-3">
              <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-10 w-10"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                >
                  <Icon name="Minus" size={18} />
                </Button>
                <span className="w-8 text-center font-bold text-lg">{quantity}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-10 w-10"
                  onClick={() => setQuantity(quantity + 1)}
                >
                  <Icon name="Plus" size={18} />
                </Button>
              </div>

              <Button 
                className="gap-2 h-11 px-6 font-semibold shadow-md hover:shadow-lg"
                onClick={handleAdd}
              >
                <Icon name="Plus" size={18} />
                Добавить в список
              </Button>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-all flex flex-col border-2 hover:border-primary/50">
      {service.image ? (
        <img src={service.image} alt={service.name} className="w-full h-40 object-cover" />
      ) : (
        <div className="w-full h-40 bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
          <Icon name={service.icon as any} size={48} className="text-primary" />
        </div>
      )}
      
      <div className="p-4 flex flex-col flex-1">
        <div className="flex-1 mb-4">
          <h3 className="font-bold text-base mb-2 line-clamp-2">{service.name}</h3>
          <p className="text-sm text-muted-foreground line-clamp-2">{service.description}</p>
        </div>
        
        <div className="space-y-3">
          {service.oldPrice && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground line-through">
                {service.oldPrice.toLocaleString()} ₽
              </span>
              {service.discount && (
                <Badge variant="destructive" className="text-xs">
                  -{service.discount}%
                </Badge>
              )}
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-primary">
              {service.price.toLocaleString()} ₽
            </span>
            
            <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
              >
                <Icon name="Minus" size={16} />
              </Button>
              <span className="w-6 text-center font-bold">{quantity}</span>
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8"
                onClick={() => setQuantity(quantity + 1)}
              >
                <Icon name="Plus" size={16} />
              </Button>
            </div>
          </div>

          <Button 
            className="w-full gap-2 h-11 font-semibold shadow-md hover:shadow-lg" 
            onClick={handleAdd}
          >
            <Icon name="Plus" size={18} />
            Добавить в список
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default ServiceCard;
