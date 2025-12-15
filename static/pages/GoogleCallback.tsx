import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { googleAuth } from '@/lib/googleAuth';
import Icon from '@/components/ui/icon';

export default function GoogleCallback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const error = params.get('error');

      if (error) {
        console.error('OAuth error:', error);
        setStatus('error');
        setTimeout(() => navigate('/orders'), 3000);
        return;
      }

      if (!code) {
        setStatus('error');
        setTimeout(() => navigate('/orders'), 3000);
        return;
      }

      try {
        const success = await googleAuth.handleCallback(code);
        if (success) {
          setStatus('success');
          setTimeout(() => navigate('/orders'), 2000);
        } else {
          setStatus('error');
          setTimeout(() => navigate('/orders'), 3000);
        }
      } catch (error) {
        console.error('Callback handling error:', error);
        setStatus('error');
        setTimeout(() => navigate('/orders'), 3000);
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        {status === 'loading' && (
          <>
            <Icon name="Loader2" size={48} className="animate-spin text-blue-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Подключение к Google...</h2>
            <p className="text-gray-600">Пожалуйста, подождите</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Icon name="CheckCircle2" size={32} className="text-green-600" />
            </div>
            <h2 className="text-xl font-semibold mb-2 text-green-600">Успешно подключено!</h2>
            <p className="text-gray-600">Перенаправление на страницу заявок...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Icon name="XCircle" size={32} className="text-red-600" />
            </div>
            <h2 className="text-xl font-semibold mb-2 text-red-600">Ошибка подключения</h2>
            <p className="text-gray-600">Перенаправление на страницу заявок...</p>
          </>
        )}
      </div>
    </div>
  );
}
