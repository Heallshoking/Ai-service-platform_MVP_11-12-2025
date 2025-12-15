import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { RoomType, ROOM_DEFAULTS, ROOM_LABELS } from '@/types/electrical';
import { useState } from 'react';

interface SurveyDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function SurveyDialog({ open, onClose }: SurveyDialogProps) {
  const [selectedRoom, setSelectedRoom] = useState<RoomType | ''>('');
  
  const defaults = selectedRoom ? ROOM_DEFAULTS[selectedRoom as RoomType] : null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Анкета для расчёта работ</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
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
              <Card className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-blue-900">
                    Среднее количество для {ROOM_LABELS[selectedRoom as RoomType].toLowerCase()}:
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
                    * Среднее значение. Выберите точное количество ниже.
                  </p>
                </div>
              </Card>

              <Button 
                onClick={onClose}
                className="w-full"
              >
                Понятно 👌🏻
              </Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}