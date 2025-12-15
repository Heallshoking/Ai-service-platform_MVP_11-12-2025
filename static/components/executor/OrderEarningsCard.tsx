import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { ExecutorEarnings } from '@/types/electrical';

interface OrderEarningsCardProps {
  earnings: ExecutorEarnings;
  isPro?: boolean;
}

export default function OrderEarningsCard({ earnings, isPro }: OrderEarningsCardProps) {
  const electricalCommission = isPro ? 50 : 30;

  return (
    <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-700">Ваш доход</h4>
          <div className="text-2xl font-bold text-green-600">
            {earnings.executorEarnings.toLocaleString()} ₽
          </div>
        </div>

        <div className="space-y-2">
          {/* Электромонтажные работы */}
          {earnings.installationWorkAmount > 0 && (
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Icon name="Wrench" className="h-4 w-4 text-amber-600" />
                <span className="text-gray-600">Электромонтаж ({electricalCommission}%)</span>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">
                  {earnings.installationEarnings.toLocaleString()} ₽
                </p>
                <p className="text-xs text-gray-500">
                  из {earnings.installationWorkAmount.toLocaleString()} ₽
                </p>
              </div>
            </div>
          )}

          {/* Другие услуги */}
          {earnings.productAmount > 0 && (
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Icon name="Package" className="h-4 w-4 text-blue-600" />
                <span className="text-gray-600">Другие услуги (50%)</span>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">
                  {earnings.productEarnings.toLocaleString()} ₽
                </p>
                <p className="text-xs text-gray-500">
                  из {earnings.productAmount.toLocaleString()} ₽
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-green-200 pt-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Итого по заказу:</span>
            <span className="font-medium text-gray-900">
              {earnings.totalAmount.toLocaleString()} ₽
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
