import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import Icon from '@/components/ui/icon';

interface Review {
  id: number;
  author: string;
  rating: number;
  comment: string;
  date: string;
}

const mockExecutor = {
  id: 1,
  name: 'Алексей Иванов',
  rating: 4.9,
  specialization: ['Электропроводка', 'Освещение', 'Розетки', 'Электрощитки'],
  completedOrders: 156,
  experience: '8 лет',
  description: 'Профессиональный электрик с большим опытом работы. Выполняю работы любой сложности качественно и в срок.',
  reviews: [
    {
      id: 1,
      author: 'Мария С.',
      rating: 5,
      comment: 'Отличная работа! Все сделано быстро и качественно.',
      date: '15.10.2024'
    },
    {
      id: 2,
      author: 'Дмитрий К.',
      rating: 5,
      comment: 'Профессионал своего дела. Рекомендую!',
      date: '10.10.2024'
    },
    {
      id: 3,
      author: 'Анна П.',
      rating: 4,
      comment: 'Хорошо выполнил работу, но немного задержался.',
      date: '05.10.2024'
    }
  ] as Review[]
};

const ExecutorPublicProfile = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const executorId = searchParams.get('id');

  const getRatingDistribution = () => {
    return [
      { stars: 5, count: 120, percentage: 77 },
      { stars: 4, count: 25, percentage: 16 },
      { stars: 3, count: 8, percentage: 5 },
      { stars: 2, count: 2, percentage: 1 },
      { stars: 1, count: 1, percentage: 1 }
    ];
  };

  return (
    <div className="min-h-screen bg-background pb-8">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
              <Icon name="ArrowLeft" size={20} />
              Назад
            </Button>
            <h1 className="font-heading font-bold text-lg">Профиль мастера</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <Avatar className="h-24 w-24">
                <AvatarFallback className="bg-primary text-primary-foreground text-3xl">
                  {mockExecutor.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1">
                <h2 className="font-bold text-2xl mb-2">{mockExecutor.name}</h2>
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <Icon name="Star" size={20} className="text-yellow-500 fill-yellow-500" />
                    <span className="font-bold text-xl">{mockExecutor.rating}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon name="CheckCircle2" size={18} />
                    <span>{mockExecutor.completedOrders} заказов</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon name="Calendar" size={18} />
                    <span>{mockExecutor.experience} опыта</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {mockExecutor.specialization.map((spec, idx) => (
                    <Badge key={idx} variant="secondary">
                      {spec}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t">
              <h3 className="font-semibold text-lg mb-2">О мастере</h3>
              <p className="text-muted-foreground">{mockExecutor.description}</p>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold text-xl mb-4">Статистика рейтинга</h3>
            <div className="space-y-3">
              {getRatingDistribution().map((item) => (
                <div key={item.stars} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 w-20">
                    <span className="text-sm font-medium">{item.stars}</span>
                    <Icon name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                  </div>
                  <Progress value={item.percentage} className="flex-1 h-2" />
                  <span className="text-sm text-muted-foreground w-12 text-right">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold text-xl mb-4">Отзывы клиентов</h3>
            <div className="space-y-4">
              {mockExecutor.reviews.map((review) => (
                <div key={review.id} className="pb-4 border-b last:border-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{review.author}</span>
                      <div className="flex items-center gap-1">
                        {Array.from({ length: review.rating }).map((_, i) => (
                          <Icon key={i} name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                        ))}
                      </div>
                    </div>
                    <span className="text-sm text-muted-foreground">{review.date}</span>
                  </div>
                  <p className="text-muted-foreground">{review.comment}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 bg-primary/5 border-primary/20">
            <div className="flex items-start gap-4">
              <Icon name="MessageCircle" size={32} className="text-primary" />
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-2">Хотите заказать у этого мастера?</h3>
                <p className="text-muted-foreground mb-4">
                  Вернитесь к оформлению заказа и выберите этого исполнителя
                </p>
                <Button onClick={() => navigate('/schedule')} size="lg" className="w-full">
                  <Icon name="ArrowLeft" size={20} className="mr-2" />
                  Вернуться к заказу
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default ExecutorPublicProfile;
