import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface CheckoutInfoCardsProps {
  finalTotal: number;
  totalDiscount: number;
  cableMeters: number;
  cableCost: number;
}

export default function CheckoutInfoCards({ 
  finalTotal, 
  totalDiscount, 
  cableMeters, 
  cableCost 
}: CheckoutInfoCardsProps) {
  return (
    <>
      <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 animate-fadeIn">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm text-green-800 font-medium mb-1">Стоимость работ</h3>
            <div className="text-3xl font-bold text-green-900">{finalTotal.toLocaleString('ru-RU')} ₽</div>
          </div>
        </div>
        {totalDiscount > 0 && (
          <div className="text-sm text-green-700 mb-2">
            ✨ Ваша экономия: {totalDiscount.toLocaleString('ru-RU')} ₽
          </div>
        )}
        {cableMeters > 0 && (
          <div className="text-sm text-green-700">
            📏 Материалы (кабель и крепёж): ~{cableCost.toLocaleString('ru-RU')} ₽
          </div>
        )}
      </Card>

      <Card className="p-6 bg-blue-50 border-blue-200 animate-fadeIn">
        <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
          <Icon name="HelpCircle" size={20} className="text-blue-600" />
          Что произойдет после оформления?
        </h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">1</div>
            <div>
              <p className="font-semibold text-gray-800">Подтверждение заявки</p>
              <p className="text-sm text-gray-600">Мастер свяжется с вами в течение часа</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">2</div>
            <div>
              <p className="font-semibold text-gray-800">Осмотр объекта</p>
              <p className="text-sm text-gray-600">Мастер приедет в указанное время для оценки</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">3</div>
            <div>
              <p className="font-semibold text-gray-800">Выполнение работ</p>
              <p className="text-sm text-gray-600">Качественно и в срок</p>
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200 animate-fadeIn">
        <div className="flex items-center gap-3 mb-3">
          <Icon name="MessageCircle" size={24} className="text-indigo-600" />
          <h3 className="font-bold text-lg">Бесплатная консультация</h3>
        </div>
        <p className="text-sm text-gray-700">
          Есть вопросы? Напишите нам во ВКонтакте — мы с радостью проконсультируем вас!
        </p>
      </Card>
    </>
  );
}
