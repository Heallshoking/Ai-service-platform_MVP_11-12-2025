import { useState } from 'react';
import { IMaskInput } from 'react-imask';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { useAuth } from '@/contexts/AuthContext';

interface LoginModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function LoginModal({ open, onClose, onSuccess }: LoginModalProps) {
  const { login, register } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<'client' | 'electrician'>('client');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const normalizePhone = (phoneValue: string): string => {
    let normalized = phoneValue.replace(/\D/g, '');
    if (normalized.startsWith('7')) {
      normalized = '8' + normalized.slice(1);
    }
    if (normalized.startsWith('9') && normalized.length === 10) {
      normalized = '8' + normalized;
    }
    return normalized;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const normalizedPhone = normalizePhone(phone);
      
      if (isRegisterMode) {
        if (!name.trim()) {
          setError('Укажите имя');
          setLoading(false);
          return;
        }
        const success = await register(normalizedPhone, password, name, role);
        if (success) {
          onSuccess?.();
          onClose();
        } else {
          setError('Ошибка регистрации');
        }
      } else {
        const success = await login(normalizedPhone, password);
        if (success) {
          onSuccess?.();
          onClose();
        } else {
          setError('Неверный телефон или пароль');
        }
      }
    } catch (err) {
      setError(isRegisterMode ? 'Ошибка регистрации' : 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPhone('');
    setPassword('');
    setName('');
    setRole('client');
    setError('');
    setIsRegisterMode(false);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">{isRegisterMode ? 'Регистрация' : 'Вход в систему'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {isRegisterMode && (
            <div>
              <label className="block text-sm font-medium mb-2">Имя</label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ваше имя"
                className="w-full"
                required
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium mb-2">Телефон</label>
            <IMaskInput
              mask="8 (000) 000-00-00"
              value={phone}
              onAccept={(value: string) => setPhone(value)}
              placeholder="8 (___) ___-__-__"
              className="w-full p-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Пароль</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••"
              className="w-full"
              required
            />
          </div>
          
          {isRegisterMode && (
            <div>
              <label className="block text-sm font-medium mb-2">Я хочу регистрацию как:</label>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant={role === 'client' ? 'default' : 'outline'}
                  className="flex-1"
                  onClick={() => setRole('client')}
                >
                  <Icon name="User" size={16} className="mr-2" />
                  Клиент
                </Button>
                <Button
                  type="button"
                  variant={role === 'electrician' ? 'default' : 'outline'}
                  className="flex-1"
                  onClick={() => setRole('electrician')}
                >
                  <Icon name="Zap" size={16} className="mr-2" />
                  Электрик
                </Button>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <Icon name="AlertCircle" size={16} className="text-red-600" />
              <span className="text-sm text-red-600">{error}</span>
            </div>
          )}

          <div className="space-y-3">
            <Button
              type="submit"
              disabled={loading}
              className="w-full"
            >
              {loading ? (isRegisterMode ? 'Регистрация...' : 'Вход...') : (isRegisterMode ? 'Зарегистрироваться' : 'Войти')}
            </Button>
            
            <Button
              type="button"
              variant="link"
              onClick={() => {
                setIsRegisterMode(!isRegisterMode);
                setError('');
              }}
              className="w-full text-sm"
            >
              {isRegisterMode ? 'Уже есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}