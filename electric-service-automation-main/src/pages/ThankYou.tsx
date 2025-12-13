import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

export default function ThankYou() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-6">
      <Card className="max-w-md w-full p-8 text-center animate-fadeIn">
        <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icon name="CheckCircle" size={48} className="text-white" />
        </div>
        
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Спасибо за заявку! 🎉
        </h1>
        
        <p className="text-gray-600 mb-3">
          Мы получили вашу заявку и скоро свяжемся с вами для уточнения деталей.
        </p>
        
        <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-gray-700 font-medium">
            ✅ Ожидайте звонка или сообщения от нашего специалиста
          </p>
        </div>
        
        <div className="space-y-3">
          <a
            href="https://t.me/konigelectric"
            target="_blank"
            rel="noopener noreferrer"
            className="block"
          >
            <Button className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold text-lg py-6">
              <Icon name="Send" size={24} className="mr-2" />
              Написать в Telegram
            </Button>
          </a>
          
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => navigate('/')}
          >
            <Icon name="Home" size={20} className="mr-2" />
            На главную
          </Button>
        </div>
        
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-700">
            <strong>Контакты для связи:</strong>
          </p>
          <a href="tel:+74012520725" className="text-blue-600 font-semibold block mt-2">
            +7 (4012) 52-07-25
          </a>
        </div>
      </Card>
    </div>
  );
}