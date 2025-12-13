import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import { PRODUCTS, Product, MASTER_VISIT_ID, calculateItemPrice } from '@/types/electrical';
import { useCart } from '@/contexts/CartContext';

interface ServiceModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ServiceModal({ open, onClose }: ServiceModalProps) {
  const navigate = useNavigate();
  const { cart, addToCart, updateQuantity, updateOption, toggleAdditionalOption } = useCart();

  const popularServices = PRODUCTS.filter(p => p.serviceCategory === 'popular' && p.id !== MASTER_VISIT_ID);
  const constructionServices = PRODUCTS.filter(p => p.serviceCategory === 'construction');

  const [expandedProduct, setExpandedProduct] = useState<string | null>(null);

  const renderServiceCard = (product: Product) => {
    const inCart = cart.find(item => item.product.id === product.id);
    const quantity = inCart?.quantity || 0;
    const isRepairSelected = inCart?.selectedOption === 'repair';
    const isInstallOrWiringSelected = inCart?.selectedOption === 'install-only' || inCart?.selectedOption === 'full-wiring';
    const showOptions = expandedProduct === product.id;

    return (
      <Card key={product.id} className="p-4 hover:shadow-lg transition-all">
        <div className="flex items-start gap-3">
          {!showOptions && (
            <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl flex-shrink-0 flex items-center justify-center border border-blue-200">
              {product.category === 'switch' ? (
                <Icon name="Power" size={28} className="text-primary" />
              ) : product.category === 'cable' ? (
                <Icon name="Cable" size={28} className="text-primary" />
              ) : product.category === 'chandelier' ? (
                <Icon name="Lightbulb" size={28} className="text-primary" />
              ) : (
                <Icon name="Plug" size={28} className="text-primary" />
              )}
            </div>
          )}
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-base mb-1">{product.name}</h3>
            <p className="text-xs text-muted-foreground mb-2">{product.description}</p>
            
            {!showOptions ? (
              <Button
                size="sm"
                onClick={() => {
                  if (quantity === 0) {
                    addToCart(product, 1);
                  }
                  setExpandedProduct(product.id);
                }}
                className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg"
              >
                <Icon name="Plus" size={16} className="mr-1" />
                Добавить
              </Button>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        if (quantity > 1) {
                          updateQuantity(product.id, quantity - 1);
                        } else {
                          setExpandedProduct(null);
                          updateQuantity(product.id, 0);
                        }
                      }}
                      className="h-9 w-9 p-0 rounded-full bg-gray-100 hover:bg-gray-200 border-2 border-gray-300"
                    >
                      <Icon name="Minus" size={16} />
                    </Button>
                    <span className="font-bold text-xl px-3 min-w-[2.5rem] text-center">{quantity}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => updateQuantity(product.id, quantity + 1)}
                      className="h-9 w-9 p-0 rounded-full bg-orange-500 hover:bg-orange-600 text-white border-0"
                    >
                      <Icon name="Plus" size={16} />
                    </Button>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setExpandedProduct(null);
                      updateQuantity(product.id, 0);
                    }}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 h-9"
                  >
                    <Icon name="Trash2" size={16} />
                  </Button>
                </div>

                <div className="space-y-1 bg-gray-50 p-3 rounded-xl border border-gray-200">
                  <p className="text-xs font-semibold text-gray-700 mb-2">Дополнительно:</p>
                  
                  {product.options?.map(option => {
                    const isRepairOption = option.id === 'repair';
                    const disabled = isRepairOption && isInstallOrWiringSelected;

                    return (
                      <div 
                        key={option.id} 
                        className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                          (isRepairOption && inCart?.selectedOption === 'repair') || 
                          (!isRepairOption && inCart?.additionalOptions?.includes(option.id))
                            ? 'bg-green-100 shadow-sm' 
                            : 'bg-white hover:bg-gray-50'
                        } ${disabled ? 'opacity-50' : ''}`}
                        onClick={() => {
                          if (!disabled) {
                            if (isRepairOption) {
                              updateOption(product.id, 'repair');
                            } else {
                              toggleAdditionalOption(product.id, option.id);
                            }
                          }
                        }}
                      >
                        <Checkbox
                          id={`${product.id}-${option.id}`}
                          checked={
                            isRepairOption
                              ? inCart?.selectedOption === 'repair'
                              : inCart?.additionalOptions?.includes(option.id)
                          }
                          disabled={disabled}
                          className="cursor-pointer"
                        />
                        <label 
                          htmlFor={`${product.id}-${option.id}`} 
                          className="text-sm cursor-pointer flex-1 font-medium"
                        >
                          {option.name}
                        </label>
                        <span className="text-sm font-bold text-green-600">
                          +{option.price} ₽
                        </span>
                      </div>
                    );
                  })}
                  
                  {product.category !== 'cable' && (
                    <>
                      <div 
                        className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                          inCart?.selectedOption === 'install-only'
                            ? 'bg-green-100 shadow-sm' 
                            : 'bg-white hover:bg-gray-50'
                        } ${isRepairSelected ? 'opacity-50' : ''}`}
                        onClick={() => !isRepairSelected && updateOption(product.id, 'install-only')}
                      >
                        <Checkbox
                          id={`${product.id}-install`}
                          checked={inCart?.selectedOption === 'install-only'}
                          disabled={isRepairSelected}
                          className="cursor-pointer"
                        />
                        <label htmlFor={`${product.id}-install`} className="text-sm cursor-pointer flex-1 font-medium">
                          Установить {product.name.toLowerCase()}
                        </label>
                        {product.priceInstallOnly > 0 && (
                          <span className="text-sm font-bold text-green-600">
                            +{product.priceInstallOnly} ₽
                          </span>
                        )}
                        {product.priceInstallOnly === 0 && product.slots > 1 && (
                          <span className="text-xs text-gray-500">
                            250 ₽/штука
                          </span>
                        )}
                      </div>
                      
                      <div 
                        className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                          inCart?.selectedOption === 'full-wiring'
                            ? 'bg-green-100 shadow-sm' 
                            : 'bg-white hover:bg-gray-50'
                        } ${isRepairSelected ? 'opacity-50' : ''}`}
                        onClick={() => !isRepairSelected && updateOption(product.id, 'full-wiring')}
                      >
                        <Checkbox
                          id={`${product.id}-wiring`}
                          checked={inCart?.selectedOption === 'full-wiring'}
                          disabled={isRepairSelected}
                          className="cursor-pointer"
                        />
                        <label htmlFor={`${product.id}-wiring`} className="text-sm cursor-pointer flex-1 font-medium">
                          Электромонтаж
                        </label>
                        <span className="text-sm font-bold text-green-600">
                          +{product.priceWithWiring} ₽
                        </span>
                      </div>
                    </>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 mt-3 border-t-2 border-orange-200">
                  <span className="text-base font-semibold">Итого за услугу:</span>
                  <span className="font-bold text-2xl bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                    {inCart ? calculateItemPrice(inCart).toLocaleString('ru-RU') : '0'} ₽
                  </span>
                </div>
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
        <DialogHeader className="relative sr-only">
          <DialogTitle>Выберите услуги</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-lg mb-3 text-gray-800">Популярные услуги</h3>
            <div className="space-y-3">
              {popularServices.map(renderServiceCard)}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-3 text-gray-800">
              Строительные услуги
            </h3>
            <p className="text-xs text-muted-foreground mb-3">
              Этими услугами пользуются дизайнеры интерьеров
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
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 h-12 text-base font-bold"
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