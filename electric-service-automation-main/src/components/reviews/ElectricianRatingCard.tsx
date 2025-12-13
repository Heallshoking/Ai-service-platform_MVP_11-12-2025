import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { ElectricianRating } from '@/types/review';

interface ElectricianRatingCardProps {
  rating: ElectricianRating;
}

export default function ElectricianRatingCard({ rating }: ElectricianRatingCardProps) {
  const renderStars = (value: number) => {
    const fullStars = Math.floor(value);
    const hasHalfStar = value % 1 >= 0.5;
    
    return (
      <div className="flex gap-1">
        {[...Array(5)].map((_, i) => {
          if (i < fullStars) {
            return (
              <Icon
                key={i}
                name="Star"
                size={20}
                className="text-yellow-400 fill-yellow-400"
              />
            );
          } else if (i === fullStars && hasHalfStar) {
            return (
              <div key={i} className="relative">
                <Icon name="Star" size={20} className="text-gray-300" />
                <div className="absolute inset-0 overflow-hidden w-1/2">
                  <Icon name="Star" size={20} className="text-yellow-400 fill-yellow-400" />
                </div>
              </div>
            );
          } else {
            return <Icon key={i} name="Star" size={20} className="text-gray-300" />;
          }
        })}
      </div>
    );
  };

  return (
    <Card className="p-6 bg-gradient-to-br from-yellow-50 to-orange-50">
      <div className="flex items-start gap-4">
        <div className="w-16 h-16 bg-gradient-to-br from-yellow-500 to-orange-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          {rating.electricianName[0].toUpperCase()}
        </div>
        
        <div className="flex-1">
          <h3 className="text-xl font-bold mb-2">{rating.electricianName}</h3>
          
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2">
              {renderStars(rating.averageRating)}
              <span className="text-2xl font-bold text-gray-800">
                {rating.averageRating.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="flex gap-6 text-sm">
            <div>
              <p className="text-gray-600">Отзывов</p>
              <p className="font-bold text-lg">{rating.totalReviews}</p>
            </div>
            <div>
              <p className="text-gray-600">Выполнено заказов</p>
              <p className="font-bold text-lg">{rating.completedOrders}</p>
            </div>
          </div>
        </div>

        <div className="text-center bg-white rounded-lg px-4 py-2 shadow-sm">
          <Icon name="Award" size={32} className="text-yellow-500 mx-auto mb-1" />
          <p className="text-xs text-gray-600">Проверенный</p>
          <p className="text-xs text-gray-600">мастер</p>
        </div>
      </div>
    </Card>
  );
}
