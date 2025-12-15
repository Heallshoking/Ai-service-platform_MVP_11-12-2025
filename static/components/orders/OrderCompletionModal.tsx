import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import Icon from '@/components/ui/icon';
import OrderEarningsCard from '@/components/executor/OrderEarningsCard';
import { Order, ExecutorProfile, calculateExecutorEarnings } from '@/types/electrical';

interface OrderCompletionModalProps {
  order: Order;
  executorProfile: ExecutorProfile;
  onConfirm: (notes?: string) => void;
  onCancel: () => void;
}

export default function OrderCompletionModal({ 
  order, 
  executorProfile,
  onConfirm, 
  onCancel 
}: OrderCompletionModalProps) {
  const [adminNotes, setAdminNotes] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  
  const earnings = calculateExecutorEarnings(order, executorProfile);

  return (
    <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
      <Card className="max-w-lg w-full p-6 space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b">
          <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
            <Icon name="CheckCircle" className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Подтвердить завершение</h3>
            <p className="text-sm text-gray-600">Заявка #{order.id.slice(-6)}</p>
          </div>
        </div>

        {/* Информация о заказе */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Исполнитель:</span>
            <span className="font-medium">{order.assignedToName || 'Не назначен'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Сумма заказа:</span>
            <span className="font-medium">{order.totalAmount?.toLocaleString()} ₽</span>
          </div>
        </div>

        {/* Расчет дохода */}
        <OrderEarningsCard earnings={earnings} isPro={executorProfile.isPro} />

        {/* Подтверждение */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Icon name="AlertTriangle" className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="flex-1 space-y-2">
              <p className="text-sm text-yellow-900 font-medium">
                Подтверждение администратора
              </p>
              <p className="text-xs text-yellow-800">
                Убедитесь, что работы выполнены в полном объеме и расчеты с клиентом произведены
              </p>
              <div className="flex items-center gap-2 mt-3">
                <input
                  type="checkbox"
                  id="confirm-completion"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <Label htmlFor="confirm-completion" className="text-sm cursor-pointer">
                  Подтверждаю, что работы выполнены и оплачены
                </Label>
              </div>
            </div>
          </div>
        </div>

        {/* Комментарий администратора */}
        <div className="space-y-2">
          <Label htmlFor="admin-notes" className="text-sm font-medium">
            Комментарий (необязательно)
          </Label>
          <Textarea
            id="admin-notes"
            placeholder="Добавьте заметки о завершении заказа..."
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            rows={3}
            className="resize-none"
          />
        </div>

        {/* Кнопки */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onCancel}
            className="flex-1"
          >
            Отмена
          </Button>
          <Button
            onClick={() => onConfirm(adminNotes || undefined)}
            disabled={!confirmed}
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            <Icon name="Check" className="h-4 w-4 mr-2" />
            Завершить заказ
          </Button>
        </div>

        {!confirmed && (
          <p className="text-xs text-center text-gray-500">
            Поставьте галочку для подтверждения завершения
          </p>
        )}
      </Card>
    </div>
  );
}
