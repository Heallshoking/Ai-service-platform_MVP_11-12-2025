import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface TelegramAuthButtonProps {
  role: 'client' | 'executor';
  onSuccess?: () => void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: any;
        ready: () => void;
        expand: () => void;
        close: () => void;
      };
    };
  }
}

export default function TelegramAuthButton({ role, onSuccess }: TelegramAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isTelegramAvailable, setIsTelegramAvailable] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      setIsTelegramAvailable(true);
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  const handleTelegramAuth = async () => {
    if (!window.Telegram?.WebApp?.initData) {
      toast({
        title: 'Ошибка',
        description: 'Откройте приложение через Telegram',
        variant: 'destructive'
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('https://functions.poehali.dev/bf3448cf-216e-4b95-882c-e2d877a5c34d', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          initData: window.Telegram.WebApp.initData,
          role
        })
      });

      if (!response.ok) {
        throw new Error('Ошибка авторизации');
      }

      const data = await response.json();

      if (data.success && data.user) {
        login({
          uid: data.user.uid,
          name: data.user.name,
          email: data.user.username ? `${data.user.username}@telegram` : undefined,
          role: data.user.role,
          photoURL: data.user.photo_url
        });

        toast({
          title: 'Успешно!',
          description: `Добро пожаловать, ${data.user.name}!`
        });

        onSuccess?.();
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось войти через Telegram',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFallbackAuth = () => {
    const mockUser = {
      uid: `demo_${role}_${Date.now()}`,
      name: role === 'executor' ? 'Демо Исполнитель' : 'Демо Клиент',
      email: `demo_${role}@example.com`,
      role: role === 'executor' ? 'executor' : 'client' as any,
      photoURL: undefined
    };

    login(mockUser);

    toast({
      title: 'Демо режим',
      description: `Вход выполнен как ${mockUser.name}`
    });

    onSuccess?.();
  };

  if (!isTelegramAvailable) {
    return (
      <Button
        onClick={handleFallbackAuth}
        disabled={isLoading}
        className="w-full"
        size="lg"
      >
        <Icon name="User" className="mr-2 h-5 w-5" />
        {isLoading ? 'Вход...' : `Войти как ${role === 'executor' ? 'исполнитель' : 'клиент'}`}
      </Button>
    );
  }

  return (
    <Button
      onClick={handleTelegramAuth}
      disabled={isLoading}
      className="w-full bg-[#0088cc] hover:bg-[#006699]"
      size="lg"
    >
      <Icon name="Send" className="mr-2 h-5 w-5" />
      {isLoading ? 'Вход...' : 'Войти через Telegram'}
    </Button>
  );
}
