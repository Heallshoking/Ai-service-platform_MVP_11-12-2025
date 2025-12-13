import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { Order, Payment, PaymentMethod, PaymentStatus } from '@/types/electrical';
import { usePermissions } from '@/hooks/usePermissions';

interface PaymentManagerProps {
  order: Order;
  onAddPayment: (orderId: string, payment: Omit<Payment, 'id' | 'createdAt'>) => void;
  onUpdatePaymentStatus: (orderId: string, paymentId: string, status: PaymentStatus) => void;
}

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  'cash': 'Наличные',
  'card': 'Банковская карта',
  'bank_transfer': 'Банковский перевод',
  'yookassa': 'ЮКassa',
  'tinkoff': 'Тинькофф',
  'sberbank': 'Сбербанк Онлайн'
};

const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  'unpaid': 'Не оплачено',
  'partially_paid': 'Частично оплачено',
  'paid': 'Оплачено',
  'refunded': 'Возврат',
  'pending': 'Ожидает подтверждения'
};

const PAYMENT_STATUS_COLORS: Record<PaymentStatus, string> = {
  'unpaid': 'bg-red-100 text-red-800 border-red-300',
  'partially_paid': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'paid': 'bg-green-100 text-green-800 border-green-300',
  'refunded': 'bg-gray-100 text-gray-800 border-gray-300',
  'pending': 'bg-blue-100 text-blue-800 border-blue-300'
};

export default function PaymentManager({ order, onAddPayment, onUpdatePaymentStatus }: PaymentManagerProps) {
  const permissions = usePermissions();
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash');
  const [paymentDescription, setPaymentDescription] = useState('');

  const totalAmount = order.totalAmount || 0;
  const paidAmount = order.paidAmount || 0;
  const remainingAmount = totalAmount - paidAmount;
  const paymentProgress = totalAmount > 0 ? (paidAmount / totalAmount) * 100 : 0;

  const handleAddPayment = () => {
    const amount = parseFloat(paymentAmount);
    if (isNaN(amount) || amount <= 0) {
      alert('Введите корректную сумму');
      return;
    }

    const payment: Omit<Payment, 'id' | 'createdAt'> = {
      amount,
      method: paymentMethod,
      status: 'paid',
      description: paymentDescription || undefined,
    };

    onAddPayment(order.id, payment);
    setPaymentAmount('');
    setPaymentDescription('');
    setShowAddPayment(false);
  };

  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          <Icon name="CreditCard" size={20} className="text-primary" />
          Оплата
        </h3>
        <span className={`text-xs font-semibold py-1 px-3 rounded-full border ${PAYMENT_STATUS_COLORS[order.paymentStatus || 'unpaid']}`}>
          {PAYMENT_STATUS_LABELS[order.paymentStatus || 'unpaid']}
        </span>
      </div>

      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm text-gray-600">Оплачено</p>
            <p className="text-2xl font-bold text-green-600">{paidAmount.toLocaleString()} ₽</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Всего</p>
            <p className="text-2xl font-bold text-gray-800">{totalAmount.toLocaleString()} ₽</p>
          </div>
        </div>
        
        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <div>
              <span className="text-xs font-semibold inline-block text-primary">
                {paymentProgress.toFixed(0)}%
              </span>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold inline-block text-orange-600">
                Осталось: {remainingAmount.toLocaleString()} ₽
              </span>
            </div>
          </div>
          <div className="overflow-hidden h-2 mb-4 text-xs flex rounded-full bg-gray-200">
            <div 
              style={{ width: `${paymentProgress}%` }} 
              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500"
            />
          </div>
        </div>
      </div>

      {order.payments && order.payments.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">История платежей</h4>
          {order.payments.map((payment) => (
            <div key={payment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Icon name="Receipt" size={14} className="text-gray-500" />
                  <span className="text-sm font-semibold">{payment.amount.toLocaleString()} ₽</span>
                  <span className="text-xs text-gray-500">{PAYMENT_METHOD_LABELS[payment.method]}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(payment.createdAt).toLocaleString('ru-RU')}
                </p>
                {payment.description && (
                  <p className="text-xs text-gray-600 mt-1">{payment.description}</p>
                )}
              </div>
              <span className={`text-xs px-2 py-1 rounded-full border ${PAYMENT_STATUS_COLORS[payment.status]}`}>
                {PAYMENT_STATUS_LABELS[payment.status]}
              </span>
            </div>
          ))}
        </div>
      )}

      {permissions.canEditOrders && (
        <div className="space-y-3">
          {!showAddPayment ? (
            <Button 
              onClick={() => setShowAddPayment(true)}
              className="w-full"
              variant="outline"
            >
              <Icon name="Plus" size={16} className="mr-2" />
              Добавить платеж
            </Button>
          ) : (
            <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Сумма платежа</label>
                <Input
                  type="number"
                  placeholder="Введите сумму"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Способ оплаты</label>
                <Select value={paymentMethod} onValueChange={(v) => setPaymentMethod(v as PaymentMethod)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PAYMENT_METHOD_LABELS).map(([key, label]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Примечание (опционально)</label>
                <Input
                  placeholder="Комментарий к платежу"
                  value={paymentDescription}
                  onChange={(e) => setPaymentDescription(e.target.value)}
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={handleAddPayment} className="flex-1">
                  <Icon name="Check" size={16} className="mr-2" />
                  Добавить
                </Button>
                <Button onClick={() => setShowAddPayment(false)} variant="outline">
                  Отмена
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
