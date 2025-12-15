import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useCart } from '@/contexts/CartContext';
import { PRODUCTS, CartItem } from '@/types/electrical';
import { ServiceContainer } from './types';
import { getInitialContainers } from './initialContainers';

function loadContainersFromCart(cart: CartItem[]): ServiceContainer[] {
  const containers = getInitialContainers();
  
  cart.forEach(cartItem => {
    const productId = cartItem.product.id;
    
    if (productId === 'auto-cable-wiring') {
      return;
    }
    
    containers.forEach(container => {
      if (productId.startsWith(container.productId + '-')) {
        const optionId = productId.substring(container.productId.length + 1);
        const option = container.options.find(opt => opt.id === optionId);
        
        if (option) {
          option.enabled = true;
          option.quantity = cartItem.quantity;
          
          if (option.id === 'replace-switch' || option.id === 'replace-outlet' || option.id === 'install') {
            const qty = cartItem.quantity;
            if (qty >= 21) {
              option.discount = { minQuantity: 21, percent: 20 };
            } else if (qty >= 11) {
              option.discount = { minQuantity: 11, percent: 15 };
            } else if (qty >= 6) {
              option.discount = { minQuantity: 6, percent: 10 };
            } else if (qty >= 3) {
              option.discount = { minQuantity: 3, percent: 5 };
            } else {
              option.discount = undefined;
            }
          }
        }
      }
    });
  });
  
  return containers;
}

export function useProductsLogic() {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToCart, cart, clearCart } = useCart();
  const [containers, setContainers] = useState<ServiceContainer[]>(() => loadContainersFromCart(cart));

  useEffect(() => {
    const newContainers = loadContainersFromCart(cart);
    setContainers(newContainers);
  }, [location.pathname]);

  const toggleContainer = (containerIndex: number) => {
    setContainers(prev => prev.map((container, idx) => {
      if (idx === containerIndex) {
        return { ...container, expanded: !container.expanded };
      }
      if (container.sectionCategory === 'wiring' && prev[containerIndex].sectionCategory === 'wiring') {
        return container;
      }
      if (prev[containerIndex].sectionCategory === 'wiring' && prev[containerIndex].expanded === false) {
        return { ...container, expanded: false };
      }
      return container;
    }));
  };

  const toggleOption = (containerIndex: number, optionId: string) => {
    setContainers(prev => prev.map((container, idx) => {
      if (idx === containerIndex) {
        const updatedOptions = container.options.map(opt => 
          opt.id === optionId ? { ...opt, enabled: !opt.enabled } : opt
        );
        
        const hasAnyEnabled = updatedOptions.some(opt => opt.enabled && !opt.isInfo);
        
        const finalOptions = updatedOptions.map(opt => {
          if (opt.id === 'equipment-fee') {
            return { ...opt, enabled: hasAnyEnabled };
          }
          return opt;
        });
        
        return {
          ...container,
          options: finalOptions
        };
      }
      return container;
    }));
  };

  const updateOptionQuantity = (containerIndex: number, optionId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      setContainers(prev => prev.map((container, idx) => {
        if (idx === containerIndex) {
          const updatedOptions = container.options.map(opt => 
            opt.id === optionId ? { ...opt, enabled: false, quantity: 1 } : opt
          );
          
          const hasAnyEnabled = updatedOptions.some(opt => opt.enabled && !opt.isInfo);
          
          const finalOptions = updatedOptions.map(opt => {
            if (opt.id === 'equipment-fee') {
              return { ...opt, enabled: hasAnyEnabled };
            }
            return opt;
          });
          
          return {
            ...container,
            options: finalOptions
          };
        }
        return container;
      }));
      return;
    }
    setContainers(prev => prev.map((container, idx) => {
      if (idx === containerIndex) {
        return {
          ...container,
          options: container.options.map(opt => {
            if (opt.id === optionId) {
              const updatedOpt = { ...opt, quantity: newQuantity };
              // Упрощенная система скидок: максимум 15%
              if (opt.id === 'replace-switch' || opt.id === 'replace-outlet' || opt.id === 'install') {
                if (newQuantity >= 10) {
                  updatedOpt.discount = { minQuantity: 10, percent: 15 };
                } else if (newQuantity >= 5) {
                  updatedOpt.discount = { minQuantity: 5, percent: 10 };
                } else {
                  updatedOpt.discount = undefined;
                }
              }
              return updatedOpt;
            }
            return opt;
          })
        };
      }
      return container;
    }));
  };

  const updateVoltage = (containerIndex: number, optionId: string, voltage: '220V' | '380V') => {
    setContainers(prev => prev.map((container, idx) => {
      if (idx === containerIndex) {
        return {
          ...container,
          options: container.options.map(opt => {
            if (opt.id === optionId && opt.voltageOptions) {
              return { 
                ...opt, 
                selectedVoltage: voltage,
                price: opt.voltageOptions[voltage]
              };
            }
            return opt;
          })
        };
      }
      return container;
    }));
  };

  const calculateContainerTotal = (container: ServiceContainer) => {
    return container.options
      .filter(opt => opt.enabled && !opt.customPrice)
      .reduce((sum, opt) => {
        let price = opt.price * opt.quantity;
        
        if (opt.discount && opt.quantity >= opt.discount.minQuantity) {
          price = price * (1 - opt.discount.percent / 100);
        }
        
        return sum + price;
      }, 0);
  };

  const calculateGrandTotal = () => {
    let total = containers.reduce((sum, container) => sum + calculateContainerTotal(container), 0);
    
    if (hasWiringOptions) {
      const cableMeters = calculateEstimatedCableMeters();
      const cablePrice = cableMeters * 100;
      
      let cableDiscount = 0;
      if (cableMeters > 200) {
        cableDiscount = 0.20;
      } else if (cableMeters > 100) {
        cableDiscount = 0.10;
      } else if (cableMeters > 50) {
        cableDiscount = 0.05;
      }
      
      total += cablePrice * (1 - cableDiscount);
    }
    
    return total;
  };

  const handleAddToCart = () => {
    clearCart();
    
    const wiringProduct = PRODUCTS.find(p => p.id === 'chandelier-1');
    
    if (hasWiringOptions && wiringProduct) {
      const cableMeters = calculateEstimatedCableMeters();
      const baseCablePrice = 100;
      
      let cableDiscount = 0;
      if (cableMeters > 200) {
        cableDiscount = 0.20;
      } else if (cableMeters > 100) {
        cableDiscount = 0.10;
      } else if (cableMeters > 50) {
        cableDiscount = 0.05;
      }
      
      const finalCablePrice = baseCablePrice * (1 - cableDiscount);
      
      const cableVirtualProduct: typeof wiringProduct = {
        ...wiringProduct,
        id: 'auto-cable-wiring',
        name: 'Монтаж кабеля',
        description: cableDiscount > 0 
          ? `Примерный метраж: ${cableMeters}м (скидка ${cableDiscount * 100}%)`
          : `Примерный метраж: ${cableMeters}м`,
        priceInstallOnly: finalCablePrice,
        priceWithWiring: finalCablePrice,
        discountApplied: true,
        options: []
      };
      addToCart(cableVirtualProduct, cableMeters, 'full-wiring');
    }
    
    let needsEquipmentFee = false;
    
    containers.forEach(container => {
      container.options.forEach(option => {
        if (option.enabled && !option.customPrice && !option.isInfo) {
          if (container.productId === 'wiring-complex' || option.id === 'move-switch-alt') {
            needsEquipmentFee = true;
          }
          
          let product = PRODUCTS.find(p => p.id === container.productId);
          
          if (!product) {
            product = PRODUCTS.find(p => p.id === 'chandelier-1');
          }
          
          if (product) {
            let finalPrice = option.price;
            
            if (option.discount && option.quantity >= option.discount.minQuantity) {
              finalPrice = finalPrice * (1 - option.discount.percent / 100);
            }
            
            if (option.id.startsWith('block-') || option.id === 'add-outlet' || option.id === 'move-switch' || option.id === 'move-switch-alt' || 
                option.id === 'cable-10m' || option.id === 'cable-corrugated' || option.id === 'breaker-install' || 
                option.id === 'breaker-replace' || option.id === 'meter' || option.id === 'input-cable' ||
                option.id === 'box-surface' || option.id === 'box-flush' || option.id === 'drilling-porcelain' || 
                option.id === 'electrical-install' || option.id === 'gas-sensor' || option.id === 'replace-switch' || option.id === 'replace-outlet') {
              
              const noAutoDiscount = option.id === 'add-outlet' || option.id.startsWith('block-') || 
                                     option.id === 'move-switch' || option.id === 'move-switch-alt' ||
                                     option.id === 'box-surface' || option.id === 'input-cable' ||
                                     option.id === 'gas-sensor' || option.id === 'meter' ||
                                     option.id === 'box-flush';
              
              const virtualProduct: typeof product = {
                ...product,
                id: `${container.productId}-${option.id}`,
                name: option.name,
                description: option.name,
                priceInstallOnly: finalPrice,
                priceWithWiring: finalPrice,
                discountApplied: noAutoDiscount || option.discount !== undefined
              };
              addToCart(virtualProduct, option.quantity, 'full-wiring');
            } else if (option.id === 'install' || option.id === 'crystal') {
              const virtualProduct: typeof product = {
                ...product,
                id: `${container.productId}-${option.id}`,
                name: option.name,
                description: option.name,
                priceInstallOnly: finalPrice,
                priceWithWiring: finalPrice
              };
              addToCart(virtualProduct, option.quantity, 'install-only');
            } else if (option.id === 'repair' || option.id === 'surface-outlet') {
              let contextName = option.name;
              if (option.id === 'repair') {
                if (container.productId === 'sw-install') {
                  contextName = 'Ремонт выключателя с учётом материалов';
                } else if (container.productId === 'out-install') {
                  contextName = 'Ремонт розетки с учётом материалов';
                }
              }
              const virtualProduct: typeof product = {
                ...product,
                id: `${container.productId}-${option.id}`,
                name: contextName,
                description: contextName,
                priceInstallOnly: finalPrice,
                priceWithWiring: finalPrice,
                discountApplied: option.discount !== undefined
              };
              addToCart(virtualProduct, option.quantity, 'full-wiring');
            } else if (option.id === 'dismantle' || option.id === 'assemble') {
              const virtualProduct: typeof product = {
                ...product,
                id: `${container.productId}-${option.id}`,
                name: option.name,
                description: option.name,
                priceInstallOnly: finalPrice,
                priceWithWiring: finalPrice,
                options: []
              };
              addToCart(virtualProduct, option.quantity, 'install-only');
            } else {
              addToCart(product, option.quantity);
            }
          }
        }
      });
    });
    
    if (needsEquipmentFee && wiringProduct) {
      const equipmentProduct: typeof wiringProduct = {
        ...wiringProduct,
        id: 'equipment-fee',
        name: 'Расходы на спецоборудование и материалы',
        description: 'Алмазные диски, мешки для пылесоса, газ и т.д.',
        priceInstallOnly: 2500,
        priceWithWiring: 2500,
        discountApplied: true,
        options: []
      };
      addToCart(equipmentProduct, 1, 'full-wiring');
    }
    
    navigate('/cart');
  };

  const calculateEstimatedCableMeters = () => {
    let totalPoints = 0;
    containers.forEach(container => {
      container.options.forEach(option => {
        if (option.enabled && container.sectionCategory === 'wiring' && !option.noCable) {
          totalPoints += option.quantity;
        }
      });
    });
    return Math.ceil(totalPoints * 7);
  };

  const clearAllOptions = () => {
    setContainers(getInitialContainers());
    clearCart();
  };

  const hasAnyEnabledOptions = containers.some(container => 
    container.options.some(opt => opt.enabled)
  );
  
  const hasWiringOptions = containers.some(container => 
    container.sectionCategory === 'wiring' && container.options.some(opt => opt.enabled)
  );

  const servicesContainers = containers.filter(c => c.sectionCategory === 'services');
  const wiringContainers = containers.filter(c => c.sectionCategory === 'wiring');

  return {
    containers,
    servicesContainers,
    wiringContainers,
    toggleContainer,
    toggleOption,
    updateOptionQuantity,
    updateVoltage,
    calculateContainerTotal,
    calculateGrandTotal,
    handleAddToCart,
    clearAllOptions,
    hasAnyEnabledOptions,
    hasWiringOptions,
    calculateEstimatedCableMeters
  };
}