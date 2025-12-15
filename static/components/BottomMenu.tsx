import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Icon from '@/components/ui/icon';
import { useCart } from '@/contexts/CartContext';
import ContactModal from '@/components/ContactModal';

export default function BottomMenu() {
  const navigate = useNavigate();
  const location = useLocation();
  const { cart } = useCart();
  const [showContactModal, setShowContactModal] = useState(false);
  
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

  const menuItems = [
    { id: 'home', icon: 'Home', label: 'Главная', path: '/' },
    { id: 'portfolio', icon: 'Images', label: 'Портфолио', path: 'https://vk.com/konig_electric', external: true },
    { id: 'cart', icon: 'ClipboardList', label: 'План работ', path: '/cart' },
    { id: 'contact', icon: 'Phone', label: 'Связь', path: '/contact' }
  ];

  const handleClick = (item: typeof menuItems[0]) => {
    if (item.id === 'contact') {
      setShowContactModal(true);
    } else if (item.external && item.path.startsWith('http')) {
      window.open(item.path, '_blank');
    } else {
      navigate(item.path);
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 py-2 px-4">
      <div className="flex justify-around items-center max-w-md mx-auto">
        {menuItems.map(item => {
          const isActive = !item.external && location.pathname === item.path;
          return (
            <button
              key={item.id}
              onClick={() => handleClick(item)}
              className={`flex flex-col items-center gap-1 py-2 px-3 rounded-lg transition-all ${
                isActive 
                  ? 'text-blue-600 bg-blue-50' 
                  : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <div className="relative">
                <Icon name={item.icon} size={22} />
                {item.id === 'cart' && totalItems > 0 && (
                  <span className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {totalItems}
                  </span>
                )}
              </div>
              <span className="text-xs font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
      <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
    </div>
  );
}