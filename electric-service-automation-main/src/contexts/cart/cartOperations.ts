import { CartItem, Product, ServiceOption, MASTER_VISIT_ID, PRODUCTS } from '@/types/electrical';

export const addItemToCart = (
  cart: CartItem[],
  product: Product,
  quantity: number = 1,
  option: ServiceOption = 'install-only',
  additionalOptions?: string[]
): CartItem[] => {
  const existing = cart.find(item => item.product.id === product.id);
  
  let updatedCart = cart;
  
  if (existing) {
    updatedCart = cart.map(item =>
      item.product.id === product.id
        ? { 
            ...item, 
            quantity: item.quantity + quantity,
            additionalOptions: additionalOptions || item.additionalOptions
          }
        : item
    );
  } else {
    const initialOptions: string[] = additionalOptions || [];
    updatedCart = [...cart, { product, quantity, selectedOption: option, additionalOptions: initialOptions }];
  }
  
  if (product.id !== MASTER_VISIT_ID && !updatedCart.find(item => item.product.id === MASTER_VISIT_ID)) {
    const masterVisitProduct = PRODUCTS.find(p => p.id === MASTER_VISIT_ID);
    if (masterVisitProduct) {
      updatedCart = [...updatedCart, { product: masterVisitProduct, quantity: 1, selectedOption: 'install-only', additionalOptions: [] }];
    }
  }
  
  return updatedCart;
};

export const removeItemFromCart = (cart: CartItem[], productId: string): CartItem[] => {
  const updatedCart = cart.filter(item => item.product.id !== productId);
  
  const ELECTRICAL_INSTALL_ID = 'electrical-install-total';
  const totalInstalls = calculateTotalElectricalInstalls(updatedCart);
  
  if (totalInstalls > 0) {
    return updatedCart.map(i => 
      i.product.id === ELECTRICAL_INSTALL_ID 
        ? { ...i, quantity: totalInstalls }
        : i
    );
  } else {
    return updatedCart.filter(i => i.product.id !== ELECTRICAL_INSTALL_ID);
  }
};

export const updateItemQuantity = (cart: CartItem[], productId: string, quantity: number): CartItem[] => {
  let updatedCart = cart.map(item =>
    item.product.id === productId ? { ...item, quantity } : item
  );

  const ELECTRICAL_INSTALL_ID = 'electrical-install-total';
  const totalInstalls = calculateTotalElectricalInstalls(updatedCart);
  
  if (totalInstalls > 0) {
    updatedCart = updatedCart.map(i => 
      i.product.id === ELECTRICAL_INSTALL_ID 
        ? { ...i, quantity: totalInstalls }
        : i
    );
  }

  return updatedCart;
};

export const updateItemOption = (cart: CartItem[], productId: string, option: ServiceOption): CartItem[] => {
  return cart.map(item =>
    item.product.id === productId ? { ...item, selectedOption: option } : item
  );
};

const calculateTotalElectricalInstalls = (cart: CartItem[]): number => {
  let total = 0;
  cart.forEach(item => {
    if (item.additionalOptions?.includes('install-blocks')) {
      let outletsCount = 1;
      
      if (item.product.id.includes('block-2')) outletsCount = 2;
      else if (item.product.id.includes('block-3')) outletsCount = 3;
      else if (item.product.id.includes('block-4')) outletsCount = 4;
      else if (item.product.id.includes('block-5')) outletsCount = 5;
      else if (item.product.name.includes('Добавить розетку')) outletsCount = 1;
      else if (item.product.name.includes('Выключатель перенести')) outletsCount = 1;
      
      total += outletsCount * item.quantity;
    }
  });
  return total;
};

export const toggleItemAdditionalOption = (cart: CartItem[], productId: string, optionId: string): CartItem[] => {
  let updatedCart = cart.map(item => {
    if (item.product.id === productId) {
      const options = item.additionalOptions || [];
      if (options.includes(optionId)) {
        return { ...item, additionalOptions: options.filter(id => id !== optionId) };
      } else {
        return { ...item, additionalOptions: [...options, optionId] };
      }
    }
    return item;
  });

  if (optionId === 'install-blocks') {
    const ELECTRICAL_INSTALL_ID = 'electrical-install-total';
    const totalInstalls = calculateTotalElectricalInstalls(updatedCart);
    
    if (totalInstalls > 0) {
      const existingInstall = updatedCart.find(i => i.product.id === ELECTRICAL_INSTALL_ID);
      
      if (existingInstall) {
        updatedCart = updatedCart.map(i => 
          i.product.id === ELECTRICAL_INSTALL_ID 
            ? { ...i, quantity: totalInstalls }
            : i
        );
      } else {
        const baseProduct = PRODUCTS.find(p => p.id === 'chandelier-1');
        if (baseProduct) {
          const virtualProduct: Product = {
            ...baseProduct,
            id: ELECTRICAL_INSTALL_ID,
            name: 'Электроустановка',
            description: 'Установка розеток/выключателей',
            priceInstallOnly: 250,
            priceWithWiring: 250,
            options: []
          };
          updatedCart = [...updatedCart, { 
            product: virtualProduct, 
            quantity: totalInstalls, 
            selectedOption: 'install-only',
            additionalOptions: []
          }];
        }
      }
    } else {
      updatedCart = updatedCart.filter(i => i.product.id !== ELECTRICAL_INSTALL_ID);
    }
  }

  return updatedCart;
};