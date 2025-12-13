import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import Icon from '@/components/ui/icon';
import { useAuth } from '@/contexts/AuthContext';
import LoginModal from '@/components/auth/LoginModal';

interface PageHeaderProps {
  imageUrl?: string;
}

export default function PageHeader({ imageUrl = 'https://cdn.poehali.dev/files/4b78877a-e24a-4720-b420-fafa87d6a759.jpg' }: PageHeaderProps) {
  const { user, isAuthenticated, logout, updateUser } = useAuth();
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  
  const handleActiveToggle = (checked: boolean) => {
    updateUser({ isActive: checked });
  };

  const getRoleBadge = (role: string) => {
    const badges = {
      client: { text: 'Клиент', color: 'bg-blue-100 text-blue-700' },
      electrician: { text: 'Электрик', color: 'bg-green-100 text-green-700' },
      admin: { text: 'Администратор', color: 'bg-purple-100 text-purple-700' }
    };
    return badges[role as keyof typeof badges] || badges.client;
  };

  const handleProfileClick = () => {
    if (user?.role === 'electrician') {
      navigate('/executor-profile-settings');
    } else if (user?.role === 'admin') {
      navigate('/admin');
    } else {
      navigate('/profile');
    }
  };

  return (
    <>
      <div className="relative max-w-7xl mx-auto">
        <img 
          src={imageUrl}
          alt="Калининград"
          className="w-full h-[200px] md:h-[300px] object-cover md:rounded-b-lg"
        />
        
        <div className="absolute top-4 right-4">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg">
                <button 
                  onClick={handleProfileClick}
                  className="flex items-center gap-2 hover:bg-gray-50 rounded-md px-2 py-1 -mx-2 -my-1 transition-colors group"
                  title="Перейти в личный кабинет"
                >
                  <div className="relative">
                    <Icon name="User" size={18} className="text-gray-600 group-hover:text-primary transition-colors" />
                    <Icon name="ChevronRight" size={12} className="absolute -right-1 -bottom-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold group-hover:text-primary transition-colors">Мой профиль</div>
                    <div className={`text-xs px-2 py-0.5 rounded ${getRoleBadge(user.role).color}`}>
                      {getRoleBadge(user.role).text}
                    </div>
                  </div>
                </button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={logout}
                  title="Выйти"
                >
                  <Icon name="LogOut" size={16} />
                </Button>
              </div>
            </div>
          ) : (
            <Button
              onClick={() => setShowLoginModal(true)}
              className="bg-white/95 backdrop-blur-sm text-gray-800 hover:bg-white shadow-lg hidden"
            >
              <Icon name="LogIn" size={18} className="mr-2" />
              Войти
            </Button>
          )}
        </div>
      </div>

      <LoginModal 
        open={showLoginModal} 
        onClose={() => setShowLoginModal(false)} 
      />
    </>
  );
}