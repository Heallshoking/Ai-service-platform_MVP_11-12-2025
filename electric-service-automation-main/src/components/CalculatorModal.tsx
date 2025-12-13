import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { RoomType, ROOM_DEFAULTS, ROOM_LABELS } from '@/types/electrical';

interface CalculatorModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CalculatorModal({ open, onClose }: CalculatorModalProps) {
  const navigate = useNavigate();
  const [selectedRoom, setSelectedRoom] = useState<RoomType | ''>('');

  const defaults = selectedRoom ? ROOM_DEFAULTS[selectedRoom as RoomType] : null;

  const handleContinue = () => {
    if (selectedRoom) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center">
            📋 Анкета для расчёта работ
          </DialogTitle>
          <p className="text-center text-sm text-muted-foreground">
            Рассчитайте стоимость работы за 2 минуты
          </p>
          <div className="text-center pt-2">
            <Button
              variant="link"
              size="sm"
              onClick={() => {
                onClose();
                navigate('/cart');
              }}
              className="text-xs text-blue-600 hover:text-blue-700"
            >
              <Icon name="ClipboardList" size={14} className="mr-1" />
              Перейти к плану работ
            </Button>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700">
              Выберите тип объекта
            </label>
            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value as RoomType | '')}
              className="w-full p-3 border-2 border-blue-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            >
              <option value="">-- Выберите тип --</option>
              {Object.entries(ROOM_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {defaults && (
            <>
              <Card className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 animate-fadeIn">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-blue-900">
                    📊 Среднее количество для {ROOM_LABELS[selectedRoom as RoomType].toLowerCase()}:
                  </p>
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-primary">{defaults.switches}</div>
                      <div className="text-xs text-muted-foreground">Выключателей</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-primary">{defaults.outlets}</div>
                      <div className="text-xs text-muted-foreground">Розеток</div>
                    </div>
                  </div>
                  <p className="text-xs text-blue-700 mt-2">
                    * Среднее значение. Выберите точное количество в каталоге услуг.
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 animate-fadeIn">
                <div className="flex items-start gap-3">
                  <Icon name="Lightbulb" size={24} className="text-green-600 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-green-900 mb-1">Рекомендация</h4>
                    <p className="text-sm text-green-800">
                      {selectedRoom === 'kitchen' && 'Для кухни рекомендуем отдельную линию для крупной техники'}
                      {selectedRoom === 'bathroom' && 'В ванной необходимо использовать влагозащищенные розетки'}
                      {selectedRoom === 'living-room' && 'Для гостиной продумайте размещение ТВ-зоны и освещения'}
                      {selectedRoom === 'bedroom' && 'В спальне удобно иметь выключатель у кровати'}
                      {selectedRoom === 'hallway' && 'В коридоре полезны проходные выключатели'}
                      {selectedRoom === 'office' && 'Для офиса важно достаточное количество розеток для техники'}
                      {selectedRoom === 'garage' && 'В гараже нужна отдельная линия для мощных инструментов'}
                      {selectedRoom === 'studio' && 'Для студии рекомендуем зонирование освещения'}
                      {selectedRoom === '1-room' && 'Для 1-комнатной квартиры оптимально 15-20 точек'}
                      {selectedRoom === '2-room' && 'Для 2-комнатной квартиры оптимально 25-35 точек'}
                      {selectedRoom === '3-room' && 'Для 3-комнатной квартиры оптимально 35-50 точек'}
                      {selectedRoom === 'cottage' && 'Для коттеджа необходимо продумать распределительный щит'}
                    </p>
                  </div>
                </div>
              </Card>

              <Button
                size="lg"
                onClick={handleContinue}
                className="w-full h-14 text-base font-semibold shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                Продолжить выбор услуг →
              </Button>
            </>
          )}

          {!selectedRoom && (
            <div className="text-center py-8 text-muted-foreground">
              <Icon name="ArrowUp" size={48} className="mx-auto mb-3 text-gray-300" />
              <p className="text-sm">Выберите тип объекта для расчета</p>
            </div>
          )}

          <Button
            onClick={onClose}
            variant="outline"
            className="w-full h-12"
          >
            Закрыть
          </Button>
        </div>
      </DialogContent>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </Dialog>
  );
}