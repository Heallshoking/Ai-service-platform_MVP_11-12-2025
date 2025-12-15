import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import { PRODUCTS, Product, MASTER_VISIT_ID, calculateItemPrice } from '@/types/electrical';
import { useCart } from '@/contexts/CartContext';
import { useNavigate } from 'react-router-dom';

interface ProductSelectionModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ProductSelectionModal({ open, onClose }: ProductSelectionModalProps) {
  const { cart, addToCart, updateQuantity, updateOption, toggleAdditionalOption } = useCart();
  const navigate = useNavigate();

  const popularServices = PRODUCTS.filter(p => p.serviceCategory === 'popular' && p.id !== MASTER_VISIT_ID);
  const constructionServices = PRODUCTS.filter(p => p.serviceCategory === 'construction');

  const renderServiceCard = (product: Product) => {
    const inCart = cart.find(item => item.product.id === product.id);
    const quantity = inCart?.quantity || 0;
    const isRepairSelected = inCart?.selectedOption === 'repair';
    const isInstallOrWiringSelected = inCart?.selectedOption === 'install-only' || inCart?.selectedOption === 'full-wiring';

    return (
      <Card key={product.id} className="p-4 hover:shadow-lg transition-all">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl flex-shrink-0 flex items-center justify-center border border-blue-200">
            {product.category === 'switch' ? (
              <Icon name="Power" size={32} className="text-primary" />
            ) : product.category === 'cable' ? (
              <Icon name="Cable" size={32} className="text-primary" />
            ) : product.category === 'chandelier' ? (
              <Icon name="Lightbulb" size={32} className="text-primary" />
            ) : (
              <Icon name="Plug" size={32} className="text-primary" />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-base mb-1">{product.name}</h3>
            <p className="text-xs text-muted-foreground mb-2">{product.description}</p>
            
            {quantity === 0 ? (
              <Button
                size="sm"
                onClick={() => addToCart(product, 1)}
                className="w-full bg-primary hover:bg-primary/90"
              >
                <Icon name="Plus" size={16} className="mr-1" />
                Добавить
              </Button>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateQuantity(product.id, quantity - 1)}
                  >
                    <Icon name="Minus" size={14} />
                  </Button>
                  <span className="font-semibold text-sm px-2">{quantity}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateQuantity(product.id, quantity + 1)}
                  >
                    <Icon name="Plus" size={14} />
                  </Button>
                </div>

                <div className="space-y-1">
                  {product.category !== 'cable' && (
                    <>
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id={`${product.id}-install`}
                          checked={inCart?.selectedOption === 'install-only'}
                          onCheckedChange={() => updateOption(product.id, 'install-only')}
                          disabled={isRepairSelected}
                        />
                        <label htmlFor={`${product.id}-install`} className={`text-xs cursor-pointer ${isRepairSelected ? 'opacity-50' : ''}`}>
                          {product.priceInstallOnly > 0 ? `+${product.priceInstallOnly} ₽` : '250 ₽/штука'} Установить {product.name.toLowerCase()}
                        </label>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id={`${product.id}-wiring`}
                          checked={inCart?.selectedOption === 'full-wiring'}
                          onCheckedChange={() => updateOption(product.id, 'full-wiring')}
                          disabled={isRepairSelected}
                        />
                        <label htmlFor={`${product.id}-wiring`} className={`text-xs cursor-pointer ${isRepairSelected ? 'opacity-50' : ''}`}>
                          +{product.priceWithWiring} ₽ Электромонтаж
                        </label>
                      </div>
                    </>
                  )}

                  {product.options?.map(option => {
                    const isConduitOption = option.id === 'conduit';
                    const isRepairOption = option.id === 'repair';
                    const disabled = isRepairOption && isInstallOrWiringSelected;

                    return (
                      <div key={option.id} className="flex items-center gap-2">
                        <Checkbox
                          id={`${product.id}-${option.id}`}
                          checked={
                            isRepairOption
                              ? inCart?.selectedOption === 'repair'
                              : inCart?.additionalOptions?.includes(option.id)
                          }
                          onCheckedChange={() => {
                            if (isRepairOption) {
                              updateOption(product.id, 'repair');
                            } else {
                              toggleAdditionalOption(product.id, option.id);
                            }
                          }}
                          disabled={disabled}
                        />
                        <label 
                          htmlFor={`${product.id}-${option.id}`} 
                          className={`text-xs cursor-pointer ${disabled ? 'opacity-50' : ''}`}
                        >
                          {isConduitOption ? `+${option.price} ₽ ${option.name}` : (
                            isRepairOption ? `${option.name}` : `+${option.price} ₽ ${option.name}`
                          )}
                        </label>
                      </div>
                    );
                  })}
                </div>

                {inCart && (
                  <div className="text-sm font-bold text-primary">
                    Итого за услугу: {calculateItemPrice(inCart).toLocaleString('ru-RU')} ₽
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  };

  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader className="relative">
          <DialogTitle>Выберите услуги</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-lg mb-3 text-gray-800">📌 Популярные услуги</h3>
            <div className="space-y-3">
              {popularServices.map(renderServiceCard)}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-3 text-gray-800">
              Строительные услуги
            </h3>
            <p className="text-xs text-muted-foreground mb-3">
              Этими услугами обычно пользуются дизайнеры интерьеров
            </p>
            <div className="space-y-3">
              {constructionServices.map(renderServiceCard)}
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-4 border-t sticky bottom-0 bg-white">
          {totalItems > 0 ? (
            <Button 
              onClick={() => {
                onClose();
                navigate('/cart');
              }} 
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              <Icon name="Check" size={18} className="mr-2" />
              Добавить ({totalItems})
            </Button>
          ) : (
            <Button onClick={onClose} variant="outline" className="flex-1">
              Закрыть
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}