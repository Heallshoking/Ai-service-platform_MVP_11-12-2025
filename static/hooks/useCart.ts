import { useState, useEffect } from 'react';

interface CartItem {
  id: string;
  title: string;
  price: number;
  quantity: number;
}

export const useCart = () => {
  const [cart, setCart] = useState<CartItem[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('cart');
    if (saved) {
      setCart(JSON.parse(saved));
    }
  }, []);

  const addToCart = (item: Omit<CartItem, 'quantity'>, quantity: number = 1) => {
    const updated = [...cart];
    const existing = updated.find(i => i.id === item.id);
    
    if (existing) {
      existing.quantity += quantity;
    } else {
      updated.push({ ...item, quantity });
    }
    
    setCart(updated);
    localStorage.setItem('cart', JSON.stringify(updated));
  };

  const removeFromCart = (id: string) => {
    const updated = cart.filter(i => i.id !== id);
    setCart(updated);
    localStorage.setItem('cart', JSON.stringify(updated));
  };

  const updateQuantity = (id: string, quantity: number) => {
    const updated = cart.map(i => 
      i.id === id ? { ...i, quantity: Math.max(0, quantity) } : i
    ).filter(i => i.quantity > 0);
    
    setCart(updated);
    localStorage.setItem('cart', JSON.stringify(updated));
  };

  const clearCart = () => {
    setCart([]);
    localStorage.removeItem('cart');
  };

  const getTotalCount = () => cart.reduce((sum, item) => sum + item.quantity, 0);
  
  const getTotalPrice = () => cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  return {
    cart,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    getTotalCount,
    getTotalPrice
  };
};
