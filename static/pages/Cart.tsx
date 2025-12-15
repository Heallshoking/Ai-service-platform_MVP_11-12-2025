import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Checkbox } from '@/components/ui/checkbox';
import { useCart } from '@/contexts/CartContext';
import { calculateItemPrice, getDiscount, getCableDiscount, MASTER_VISIT_ID, calculateFrames } from '@/types/electrical';
import ServiceModal from '@/components/ServiceModal';
import ContactModal from '@/components/ContactModal';

import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';

export default function Cart() {
  const navigate = useNavigate();
  const { cart, updateQuantity, removeFromCart, updateOption, toggleAdditionalOption, clearCart } = useCart();
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);

  const [editMode, setEditMode] = useState(false);

  const totalPrice = cart.reduce((sum, item) => {
    if (item.product.id === 'auto-cable-wiring') return sum;
    return sum + calculateItemPrice(item);
  }, 0);
  
  const totalDiscount = cart.reduce((sum, item) => {
    if (item.product.id === 'auto-cable-wiring') return sum;
    if (item.product.discountApplied) return sum;
    const discount = getDiscount(item.quantity);
    const basePrice = item.selectedOption === 'install-only' ? item.product.priceInstallOnly : item.product.priceWithWiring;
    const fullPrice = basePrice * item.quantity;
    return sum + (fullPrice * discount / 100);
  }, 0);

  const cableItem = cart.find(item => item.product.id === 'auto-cable-wiring');
  const cableMeters = cableItem ? cableItem.quantity : 0;
  const cableCost = cableItem ? calculateItemPrice(cableItem) : 0;
  
  const cableDiscount = getCableDiscount(cableMeters);
  const baseCableCost = cableMeters * 100;
  const cableSavings = baseCableCost - cableCost;
  
  const wiringItems = cart.filter(item => item.selectedOption === 'full-wiring' && item.product.id !== 'auto-cable-wiring');
  const totalFrames = calculateFrames(wiringItems);
  
  const finalTotal = totalPrice + cableCost;
  
  const masterVisit = cart.find(item => item.product.id === MASTER_VISIT_ID);
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  if (cart.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <PageHeader />
        
        <div className="max-w-md mx-auto">
          <PageNavigation onContactClick={() => setShowContactModal(true)} />

          <div className="p-6">
            <Card className="p-12 text-center bg-white">
              <Icon name="ShoppingCart" size={64} className="text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Задачи</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Добавьте услуги для формирования списка задач
              </p>
              <Button
                onClick={() => navigate('/products')}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                Добавить задачи
              </Button>
            </Card>
          </div>
        </div>

        <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
        <ServiceModal open={showServiceModal} onClose={() => setShowServiceModal(false)} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-32">
      <PageHeader />

      <div className="max-w-md mx-auto">
        <PageNavigation onContactClick={() => setShowContactModal(true)} />

        <div className="p-6 space-y-4">
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden animate-fadeIn">
            <div className="p-6 space-y-4">
              
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700">Задачи</h3>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (confirm('Очистить весь список задач?')) {
                        clearCart();
                      }
                    }}
                    className="text-xs text-gray-500 hover:text-red-600"
                  >
                    <Icon name="Trash2" size={14} />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditMode(!editMode)}
                    className={editMode ? "bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold shadow-lg" : "text-xs"}
                  >
                    <Icon name={editMode ? 'Check' : 'Edit'} size={14} className="mr-1" />
                    {editMode ? 'Готово' : 'Редактировать'}
                  </Button>
                </div>
              </div>

              {cart.filter(item => item.product.id !== MASTER_VISIT_ID && item.product.id !== 'auto-cable-wiring').map((item, index) => (
                <div key={item.product.id} className="border-b border-gray-200 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-gray-400">#{index + 1}</span>
                        <h4 className="font-semibold text-sm">{item.product.name}</h4>
                      </div>
                      
                      {editMode ? (
                        <div className="mt-2 space-y-2">
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                              className="h-7 w-7 p-0"
                            >
                              <Icon name="Minus" size={12} />
                            </Button>
                            <span className="text-sm font-semibold px-2">{item.quantity} ед</span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                              className="h-7 w-7 p-0"
                            >
                              <Icon name="Plus" size={12} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeFromCart(item.product.id)}
                              className="h-7 text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Icon name="Trash2" size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => navigate('/products')}
                              className="h-7 text-blue-600 hover:text-blue-700 hover:bg-blue-50 text-xs"
                              title="Вернуться к выбору услуг"
                            >
                              <Icon name="ArrowLeft" size={14} className="mr-1" />
                              К услугам
                            </Button>
                          </div>

                          <div className="space-y-1">
                            {/* Опції для світильника */}
                            {(item.product.id.includes('chandelier-1') || item.product.name.includes('светильник')) && item.product.options && item.product.options.length > 0 && (
                              item.product.options.map(option => (
                                <div key={option.id} className="flex items-center gap-2">
                                  <Checkbox
                                    id={`${item.product.id}-${option.id}`}
                                    checked={item.additionalOptions?.includes(option.id) || false}
                                    onCheckedChange={() => toggleAdditionalOption(item.product.id, option.id)}
                                  />
                                  <label htmlFor={`${item.product.id}-${option.id}`} className="text-xs cursor-pointer">
                                    +{option.price} ₽ {option.name}
                                  </label>
                                </div>
                              ))
                            )}
                            
                            {/* Опція для блоків розеток та додавання розеток/перенесення вимикачів */}
                            {(
                              (item.product.id.includes('block-') && item.product.id.startsWith('wiring-complex')) ||
                              item.product.name.includes('Добавить розетку') ||
                              item.product.name.includes('Выключатель перенести')
                            ) && (
                              <div className="flex items-center gap-2">
                                <Checkbox
                                  id={`${item.product.id}-install-blocks`}
                                  checked={item.additionalOptions?.includes('install-blocks') || false}
                                  onCheckedChange={() => toggleAdditionalOption(item.product.id, 'install-blocks')}
                                />
                                <label htmlFor={`${item.product.id}-install-blocks`} className="text-xs cursor-pointer">
                                  Установить розетки/выключатели
                                </label>
                              </div>
                            )}
                            
                            {/* Опції для електролічильника - вибір напруги */}
                            {item.product.id.includes('meter') && (
                              <div className="space-y-2">
                                <p className="text-xs text-gray-600">Напряжение:</p>
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => {
                                      // Logic for 220V will be added
                                    }}
                                    className="px-3 py-1 text-xs border rounded bg-blue-500 text-white"
                                  >
                                    220V (3500 ₽)
                                  </button>
                                  <button
                                    onClick={() => {
                                      // Logic for 380V will be added
                                    }}
                                    className="px-3 py-1 text-xs border rounded hover:bg-gray-100"
                                  >
                                    380V (5500 ₽)
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-1">
                          <p className="text-xs text-gray-600">
                            {item.additionalOptions?.includes('install') && `Установить`}
                            {item.product.category !== 'chandelier' && item.additionalOptions?.includes('wiring') && item.additionalOptions?.includes('install') && `, Добавить/перенести`}
                            {item.product.category !== 'chandelier' && item.additionalOptions?.includes('wiring') && !item.additionalOptions?.includes('install') && `Добавить/перенести`}
                            {item.additionalOptions && item.product.options && item.additionalOptions.filter(id => id !== 'install' && id !== 'wiring').length > 0 && `${item.additionalOptions?.includes('install') || item.additionalOptions?.includes('wiring') ? ', + ' : ''}${item.product.options.filter(o => item.additionalOptions?.includes(o.id)).map(o => o.name).join(', ')}`}
                          </p>
                        </div>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className="font-bold text-primary">{calculateItemPrice(item).toLocaleString('ru-RU')} ₽</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {item.quantity} {
                          item.product.id === 'auto-cable-wiring' ? 'м' :
                          item.product.name.includes('светильник') || 
                          item.product.name.includes('розет') || 
                          item.product.name.includes('выключатель') ||
                          item.product.name.includes('Добавить розетку') ||
                          item.product.name.includes('Выключатель перенести') ? 'шт' : 'ед'
                        }
                      </div>
                      {!item.product.discountApplied && getDiscount(item.quantity) > 0 && (
                        <div className="text-xs text-green-600 font-semibold">
                          Скидка {getDiscount(item.quantity)}%
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {masterVisit && (
                <div className="border-b border-gray-200 pb-4 bg-orange-50 -mx-6 px-6 py-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon name="Truck" size={18} className="text-orange-600" />
                      <span className="font-semibold text-sm">{masterVisit.product.name}</span>
                    </div>
                    <span className="font-bold text-primary">{masterVisit.product.priceInstallOnly} ₽</span>
                  </div>
                </div>
              )}

              <div className="space-y-2 pt-2">
                {cableMeters > 0 && (
                  <div className="mb-3 p-3 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
                    <div className="flex-1">
                      <div className="font-semibold text-xs text-gray-800 mb-2">
                        Автоматически добавлен монтаж кабеля
                      </div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div className="flex justify-between">
                          <span>Ориентировочный расход:</span>
                          <span className="font-semibold">~{cableMeters} метров</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Стоимость монтажа:</span>
                          <span className="font-semibold">{cableCost.toLocaleString('ru-RU')} ₽</span>
                        </div>
                        {cableDiscount > 0 && (
                          <div className="flex justify-between text-green-600">
                            <span>Скидка за объем {cableDiscount}%:</span>
                            <span className="font-bold">-{cableSavings.toLocaleString('ru-RU')} ₽</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Работы без учёта кабеля:</span>
                  <span className="font-semibold">{totalPrice.toLocaleString('ru-RU')} ₽</span>
                </div>
                
                {cableMeters > 0 && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Монтаж кабеля (~{cableMeters} м):</span>
                      <span className="font-semibold">{cableCost.toLocaleString('ru-RU')} ₽</span>
                    </div>
                    {totalFrames > 0 && (
                      <div className="flex justify-between text-sm text-gray-500">
                        <span>Потребуется рамок:</span>
                        <span>{totalFrames} шт</span>
                      </div>
                    )}
                  </>
                )}

                {(totalDiscount > 0 || cableSavings > 0) && (
                  <div className="flex justify-between text-sm">
                    <span className="text-green-600">Общая экономия:</span>
                    <span className="text-green-600 font-bold">-{(totalDiscount + cableSavings).toLocaleString('ru-RU')} ₽</span>
                  </div>
                )}

                <div className="border-t-2 border-dashed border-gray-300 pt-3 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-800">ИТОГО</span>
                    <span className="text-2xl font-bold text-primary">{finalTotal.toLocaleString('ru-RU')} ₽</span>
                  </div>
                </div>
              </div>
            </div>


          </div>

          <Button
            onClick={() => navigate('/checkout')}
            size="lg"
            className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-xl"
          >
            Перейти к оформлению
          </Button>

          <Button
            variant="outline"
            onClick={() => navigate('/products')}
            className="w-full"
          >
            <Icon name="Plus" size={16} className="mr-2" />
            Добавить еще
          </Button>
        </div>
      </div>

      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
      <ServiceModal open={showServiceModal} onClose={() => setShowServiceModal(false)} />
    </div>
  );
}