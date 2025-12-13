import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const Confirmation = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-8 text-center space-y-6">
        <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
          <Icon name="CheckCircle2" size={48} className="text-green-600" />
        </div>

        <div className="space-y-2">
          <h1 className="font-bold text-2xl">Заявка принята!</h1>
          <p className="text-muted-foreground">
            Ваша заявка успешно отправлена. Мастер свяжется с вами в ближайшее время для подтверждения встречи.
          </p>
        </div>

        <div className="bg-primary/5 rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Ожидаемое время ответа:</span>
            <span className="font-semibold">15-30 минут</span>
          </div>
        </div>

        <div className="space-y-3">
          <Button 
            className="w-full gap-2" 
            onClick={() => navigate('/order-history')}
          >
            <Icon name="FileText" size={20} />
            Посмотреть мои заявки
          </Button>
          
          <Button 
            variant="outline" 
            className="w-full" 
            onClick={() => navigate('/')}
          >
            На главную
          </Button>
        </div>

        <div className="pt-4 border-t">
          <p className="text-sm text-muted-foreground mb-3">
            Остались вопросы? Напишите нам в Telegram
          </p>
          <Button 
            variant="link" 
            className="gap-2"
            onClick={() => window.open('https://t.me/konigelectric', '_blank')}
          >
            <Icon name="Send" size={16} />
            @konigelectric
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Confirmation;
