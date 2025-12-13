import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import Icon from '@/components/ui/icon';
import { useNotifications } from '@/hooks/useNotifications';

interface PageNavigationProps {
  onContactClick?: () => void;
  showContinueButton?: boolean;
  onContinueClick?: () => void;
}

export default function PageNavigation({ onContactClick, showContinueButton = false, onContinueClick }: PageNavigationProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { cart } = useCart();
  const { user, isAuthenticated, updateUser } = useAuth();
  const permissions = usePermissions();
  const { unreadCount } = useNotifications();
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const isCheckoutPage = location.pathname === '/checkout';
  const isCartPage = location.pathname === '/cart';
  const isProductsPage = location.pathname === '/products';
  const hasItems = cart.length > 0;
  
  const handleActiveToggle = (checked: boolean) => {
    updateUser({ isActive: checked });
  };
  
  const isElectrician = user?.role === 'electrician';

  return (
    <div className="bg-white shadow-lg p-4">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
      <div className="flex items-center gap-1">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => navigate('/home')}
          title="На главную"
        >
          <Icon name="Home" size={20} />
        </Button>
        <Button 
          variant="ghost"
          className="h-10 text-sm px-3"
          onClick={() => navigate(isElectrician ? '/all-orders' : '/products')}
          title={isElectrician ? "Поиск заказов" : "Услуги электрика"}
        >
          {isElectrician ? 'Поиск заказов' : 'Услуги электрика'}
        </Button>
        {((showContinueButton && isProductsPage) || (hasItems && !isElectrician && !isCheckoutPage && !isCartPage)) && (
          <Button 
            variant="ghost"
            className="h-10 text-sm px-3 text-blue-600 font-semibold relative"
            onClick={() => {
              if (onContinueClick) {
                onContinueClick();
              } else {
                navigate('/cart');
              }
            }}
            title="Продолжить"
          >
            Продолжить
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {cartCount}
              </span>
            )}
          </Button>
        )}
        {cartCount > 0 && isCartPage && !isElectrician && (
          <Button 
            variant="ghost"
            className="h-10 text-sm px-3 text-blue-600 font-semibold relative"
            onClick={() => navigate('/checkout')}
            title="Оформить заявку"
          >
            Оформить заявку
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {cartCount}
            </span>
          </Button>
        )}
      </div>
      <div className="flex items-center gap-3">
        {isElectrician && !isCheckoutPage && !isCartPage && (
          <button 
            className="h-10 text-sm px-3 hover:bg-gray-100 rounded-md transition-colors flex items-center gap-2 cursor-pointer"
            onClick={() => handleActiveToggle(!user?.isActive)}
            title="Переключить статус"
          >
            <span className={`text-xs font-medium ${user?.isActive ? 'text-green-700' : 'text-gray-600'}`}>
              {user?.isActive ? 'Работаю' : 'Не работаю'}
            </span>
            <Switch 
              checked={user?.isActive || false}
              onCheckedChange={handleActiveToggle}
              className="data-[state=checked]:bg-green-500"
              onClick={(e) => e.stopPropagation()}
            />
          </button>
        )}
        {isAuthenticated ? (
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => navigate('/notifications')}
            title="Уведомления"
            className="relative"
          >
            <Icon name="Bell" size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </Button>
        ) : (
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => navigate('/contact')}
            title="Связаться с нами"
          >
            <Icon name="MessageCircle" size={20} />
          </Button>
        )}
      </div>
      </div>
    </div>
  );
}