import { useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';
import { calculateTotalEarnings } from '@/utils/executorEarnings';

interface EarningsWidgetProps {
  orders: Order[];
  executorId: string;
}

type Period = 'month' | '6months' | 'year';

export default function EarningsWidget({ orders, executorId }: EarningsWidgetProps) {
  const [period, setPeriod] = useState<Period>('month');

  const earnings = useMemo(() => {
    const now = new Date();
    let startDate: Date;

    switch (period) {
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case '6months':
        startDate = new Date(now.getFullYear(), now.getMonth() - 6, 1);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
    }

    return calculateTotalEarnings(orders, executorId, startDate, now);
  }, [orders, executorId, period]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">Доход</h3>
          <Tabs value={period} onValueChange={(v) => setPeriod(v as Period)}>
            <TabsList className="h-8">
              <TabsTrigger value="month" className="text-xs px-2">1 мес</TabsTrigger>
              <TabsTrigger value="6months" className="text-xs px-2">6 мес</TabsTrigger>
              <TabsTrigger value="year" className="text-xs px-2">Год</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-1 text-gray-600">
              <Icon name="CheckCircle2" className="h-3 w-3" />
              <span className="text-xs">Выполнено</span>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(earnings.totalEarnings)}
            </p>
            <p className="text-xs text-gray-500">{earnings.completedOrders} заказов</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-1 text-gray-600">
              <Icon name="Clock" className="h-3 w-3" />
              <span className="text-xs">Ожидается</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {formatCurrency(earnings.expectedEarnings)}
            </p>
            <p className="text-xs text-gray-500">
              {earnings.totalOrders - earnings.completedOrders} в работе
            </p>
          </div>
        </div>

        <div className="pt-3 border-t border-green-200">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-gray-600">Монтажные работы (30%)</p>
              <p className="font-semibold text-gray-900">
                {formatCurrency(earnings.installationEarnings)}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Товары (50%)</p>
              <p className="font-semibold text-gray-900">
                {formatCurrency(earnings.productEarnings)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
