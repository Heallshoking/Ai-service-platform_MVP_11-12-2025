import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { ExecutorProfile, RANKS } from '@/types/electrical';

interface ExecutorStatsCardProps {
  profile: ExecutorProfile;
}

export default function ExecutorStatsCard({ profile }: ExecutorStatsCardProps) {
  const currentRank = RANKS[profile.rank];
  const rankIndex = ['specialist', 'master', 'senior', 'expert', 'legend'].indexOf(profile.rank);
  const nextRank = rankIndex < 4 ? RANKS[['specialist', 'master', 'senior', 'expert', 'legend'][rankIndex + 1]] : null;

  const ordersProgress = nextRank 
    ? (profile.completedOrders / nextRank.minCompletedOrders) * 100 
    : 100;
  const revenueProgress = nextRank 
    ? (profile.totalRevenue / nextRank.minRevenue) * 100 
    : 100;

  return (
    <Card className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
      <div className="space-y-4">
        {/* Текущий статус */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-3xl">{currentRank.badge}</span>
                <h3 className="text-lg font-bold text-amber-900">{currentRank.name}</h3>
              </div>
              <p className="text-xs text-amber-700">{currentRank.description}</p>
            </div>
          </div>
          {profile.isPro && (
            <div className="bg-gradient-to-r from-purple-500 to-indigo-500 px-3 py-1.5 rounded-full shadow-md animate-pulse">
              <span className="text-xs font-bold text-white flex items-center gap-1">
                <Icon name="Award" className="h-3 w-3" />
                ПРОФИ
              </span>
            </div>
          )}
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white rounded-lg p-3 border border-amber-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-1">Специалист</h4>
            <p className="text-xl font-bold text-gray-900 mb-1">{profile.completedOrders}</p>
            <p className="text-[10px] text-gray-500 leading-tight">Выполняйте больше заказов для повышения ранга</p>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-amber-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-1">Начисления</h4>
            <p className="text-xl font-bold text-gray-900 mb-1">
              {profile.totalRevenue.toLocaleString()} ₽
            </p>
            <p className="text-[10px] text-gray-500 leading-tight">{currentRank.commission}% с заказа • Подтверждения дают +20%</p>
          </div>
        </div>

        {/* Прогресс до следующего звания */}
        {nextRank && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-amber-800">
                До статуса "{nextRank.name}"
              </span>
              <span className="text-xs text-amber-600">{nextRank.badge}</span>
            </div>
            
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-600">
                <span>Заказы: {profile.completedOrders} / {nextRank.minCompletedOrders}</span>
                <span>{Math.min(ordersProgress, 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-300"
                  style={{ width: `${Math.min(ordersProgress, 100)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-600">
                <span>Доход: {profile.totalRevenue.toLocaleString()} / {nextRank.minRevenue.toLocaleString()} ₽</span>
                <span>{Math.min(revenueProgress, 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${Math.min(revenueProgress, 100)}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Бонусы */}
        {(profile.hasCar || profile.hasTools || profile.isActive) && (
          <div className="border-t border-amber-200 pt-3">
            <p className="text-xs font-medium text-amber-800 mb-2">Активные бонусы:</p>
            <div className="flex flex-wrap gap-2">
              {profile.hasCar && (
                <div className="flex items-center gap-1 bg-blue-100 border border-blue-300 px-2 py-1 rounded-full">
                  <Icon name="Car" className="h-3 w-3 text-blue-600" />
                  <span className="text-xs font-medium text-blue-700">+10%</span>
                </div>
              )}
              {profile.hasTools && (
                <div className="flex items-center gap-1 bg-orange-100 border border-orange-300 px-2 py-1 rounded-full">
                  <Icon name="Wrench" className="h-3 w-3 text-orange-600" />
                  <span className="text-xs font-medium text-orange-700">+5%</span>
                </div>
              )}
              {profile.isActive && (
                <div className="flex items-center gap-1 bg-green-100 border border-green-300 px-2 py-1 rounded-full">
                  <Icon name="Zap" className="h-3 w-3 text-green-600" />
                  <span className="text-xs font-medium text-green-700">+5%</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}