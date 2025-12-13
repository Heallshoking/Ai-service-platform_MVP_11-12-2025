import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import TelegramAuthButton from '@/components/auth/TelegramAuthButton';
import { RANKS } from '@/types/electrical';

export default function RoleSelection() {
  const [selectedRole, setSelectedRole] = useState<'client' | 'executor' | null>(null);
  const navigate = useNavigate();

  const handleSuccess = () => {
    if (selectedRole === 'executor') {
      navigate('/orders');
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">Добро пожаловать!</h1>
          <p className="text-gray-600">Выберите свою роль для продолжения</p>
        </div>

        {!selectedRole ? (
          <div className="grid gap-4">
            <Card
              className="p-6 cursor-pointer hover:shadow-lg transition-all border-2 hover:border-blue-500"
              onClick={() => setSelectedRole('client')}
            >
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Icon name="User" className="h-6 w-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">Я клиент</h3>
                  <p className="text-sm text-gray-600">
                    Заказать электромонтажные работы, выбрать товары и следить за заявками
                  </p>
                </div>
              </div>
            </Card>

            <Card
              className="p-6 cursor-pointer hover:shadow-lg transition-all border-2 hover:border-green-500"
              onClick={() => setSelectedRole('executor')}
            >
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Icon name="Wrench" className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">Я исполнитель</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Принимать заказы, отслеживать доход и управлять своим графиком работы
                  </p>
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{RANKS.specialist.badge}</span>
                      <span className="font-semibold text-amber-900">{RANKS.specialist.name}</span>
                    </div>
                    <p className="text-xs text-amber-700 mb-2">{RANKS.specialist.description}</p>
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-amber-900">Начальные обязанности:</p>
                      {RANKS.specialist.responsibilities.slice(0, 3).map((resp, idx) => (
                        <div key={idx} className="flex items-center gap-1 text-xs text-amber-700">
                          <Icon name="Check" className="h-3 w-3" />
                          <span>{resp}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {selectedRole === 'executor' ? 'Вход как исполнитель' : 'Вход как клиент'}
                </h3>
                <button
                  onClick={() => setSelectedRole(null)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Изменить
                </button>
              </div>

              <div className="space-y-3">
                <TelegramAuthButton role={selectedRole} onSuccess={handleSuccess} />
                
                <div className="text-center text-xs text-gray-500">
                  {selectedRole === 'executor' 
                    ? 'После входа вы сможете принимать заказы и отслеживать свой доход'
                    : 'После входа вы сможете создавать заявки и отслеживать их статус'
                  }
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}