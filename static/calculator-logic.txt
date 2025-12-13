import { Card } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';

interface CalculatorTabProps {
  scenario: 'A' | 'B' | null;
  setScenario: (scenario: 'A' | 'B' | null) => void;
  repairType: string;
  setRepairType: (type: string) => void;
  calcType: string;
  setCalcType: (type: string) => void;
  switchCount: number;
  setSwitchCount: (count: number) => void;
  socketCount: number;
  setSocketCount: (count: number) => void;
  lightingType: string;
  setLightingType: (type: string) => void;
  powerEquipment: string[];
  setPowerEquipment: (equipment: string[]) => void;
  installType: string;
  setInstallType: (type: string) => void;
  hasWires: string;
  setHasWires: (value: string) => void;
}

export default function CalculatorTab({
  scenario,
  setScenario,
  repairType,
  setRepairType,
  calcType,
  setCalcType,
  switchCount,
  setSwitchCount,
  socketCount,
  setSocketCount,
  lightingType,
  setLightingType,
  powerEquipment,
  setPowerEquipment,
  installType,
  setInstallType,
  hasWires,
  setHasWires
}: CalculatorTabProps) {
  const calculateEstimate = () => {
    let total = 0;
    
    if (scenario === 'A') {
      if (repairType === 'cosmetic') {
        total = switchCount * 400 + socketCount * 500;
        if (lightingType === 'chandelier') total += 800;
        if (lightingType === 'spots') total += 1200;
        if (powerEquipment.includes('washer')) total += 1500;
        if (powerEquipment.includes('dishwasher')) total += 1500;
        if (powerEquipment.includes('oven')) total += 2000;
      } else if (repairType === 'major') {
        const basePrice = calcType === 'simple' ? 1200 : 1800;
        const totalPoints = switchCount + socketCount;
        total = totalPoints * basePrice;
        
        if (lightingType === 'spots') total += totalPoints * 200;
        if (powerEquipment.length > 0) total += powerEquipment.length * 1500;
        if (installType === 'concealed') total += totalPoints * 300;
      }
    } else if (scenario === 'B') {
      total = switchCount * 250 + socketCount * 250;
      
      if (hasWires === 'yes') {
        total *= 0.7;
      } else if (hasWires === 'partial') {
        total *= 0.85;
      }
    }
    
    return Math.round(total);
  };

  const handlePowerEquipmentToggle = (item: string) => {
    if (powerEquipment.includes(item)) {
      setPowerEquipment(powerEquipment.filter(i => i !== item));
    } else {
      setPowerEquipment([...powerEquipment, item]);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-24">
      <div className="text-center space-y-2">
        <h2 className="font-heading text-2xl md:text-3xl font-bold text-foreground">
          Калькулятор стоимости
        </h2>
        <p className="text-muted-foreground text-sm">Рассчитайте примерную стоимость работ</p>
      </div>

      <Card className="p-6 space-y-6 bg-card">
        <div className="space-y-4">
          <Label className="text-base font-semibold">Что вам нужно?</Label>
          <RadioGroup value={scenario || ''} onValueChange={(v) => setScenario(v as 'A' | 'B')}>
            <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-accent transition-colors cursor-pointer">
              <RadioGroupItem value="A" id="scenario-a" />
              <Label htmlFor="scenario-a" className="flex-1 cursor-pointer">
                <div className="font-medium">Провести электрику в квартире с нуля</div>
                <p className="text-xs text-muted-foreground mt-1">Для новостроек и капитального ремонта</p>
              </Label>
            </div>
            <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-accent transition-colors cursor-pointer">
              <RadioGroupItem value="B" id="scenario-b" />
              <Label htmlFor="scenario-b" className="flex-1 cursor-pointer">
                <div className="font-medium">Установить розетки/выключатели</div>
                <p className="text-xs text-muted-foreground mt-1">Когда проводка уже есть</p>
              </Label>
            </div>
          </RadioGroup>
        </div>

        {scenario === 'A' && (
          <>
            <div className="space-y-3">
              <Label>Тип ремонта</Label>
              <Select value={repairType} onValueChange={setRepairType}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите тип ремонта" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cosmetic">Косметический (только установка)</SelectItem>
                  <SelectItem value="major">Капитальный (проводка + установка)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {repairType === 'major' && (
              <>
                <div className="space-y-3">
                  <Label>Тип расчёта</Label>
                  <RadioGroup value={calcType} onValueChange={setCalcType}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="simple" id="calc-simple" />
                      <Label htmlFor="calc-simple" className="cursor-pointer">
                        Упрощённый (дешевле, но менее детальный)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="detailed" id="calc-detailed" />
                      <Label htmlFor="calc-detailed" className="cursor-pointer">
                        Детальный (точнее, но дороже)
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-3">
                  <Label>Тип монтажа</Label>
                  <Select value={installType} onValueChange={setInstallType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите тип монтажа" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="surface">Открытая проводка</SelectItem>
                      <SelectItem value="concealed">Скрытая проводка</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Выключатели</Label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSwitchCount(Math.max(0, switchCount - 1))}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Minus" size={16} />
                  </button>
                  <span className="flex-1 text-center font-bold text-lg">{switchCount}</span>
                  <button
                    onClick={() => setSwitchCount(switchCount + 1)}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Plus" size={16} />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Розетки</Label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSocketCount(Math.max(0, socketCount - 1))}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Minus" size={16} />
                  </button>
                  <span className="flex-1 text-center font-bold text-lg">{socketCount}</span>
                  <button
                    onClick={() => setSocketCount(socketCount + 1)}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Plus" size={16} />
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <Label>Освещение</Label>
              <Select value={lightingType} onValueChange={setLightingType}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите тип освещения" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Не требуется</SelectItem>
                  <SelectItem value="chandelier">Люстра</SelectItem>
                  <SelectItem value="spots">Точечные светильники</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>Мощная техника</Label>
              <div className="space-y-2">
                {[
                  { id: 'washer', label: 'Стиральная машина' },
                  { id: 'dishwasher', label: 'Посудомоечная машина' },
                  { id: 'oven', label: 'Электроплита/духовка' }
                ].map(item => (
                  <div key={item.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={item.id}
                      checked={powerEquipment.includes(item.id)}
                      onCheckedChange={() => handlePowerEquipmentToggle(item.id)}
                    />
                    <Label htmlFor={item.id} className="cursor-pointer">{item.label}</Label>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {scenario === 'B' && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Выключатели</Label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSwitchCount(Math.max(0, switchCount - 1))}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Minus" size={16} />
                  </button>
                  <span className="flex-1 text-center font-bold text-lg">{switchCount}</span>
                  <button
                    onClick={() => setSwitchCount(switchCount + 1)}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Plus" size={16} />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Розетки</Label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSocketCount(Math.max(0, socketCount - 1))}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Minus" size={16} />
                  </button>
                  <span className="flex-1 text-center font-bold text-lg">{socketCount}</span>
                  <button
                    onClick={() => setSocketCount(socketCount + 1)}
                    className="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-accent"
                  >
                    <Icon name="Plus" size={16} />
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <Label>Есть ли провода в стенах?</Label>
              <RadioGroup value={hasWires} onValueChange={setHasWires}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="yes" id="wires-yes" />
                  <Label htmlFor="wires-yes" className="cursor-pointer">Да, провода уже есть</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="partial" id="wires-partial" />
                  <Label htmlFor="wires-partial" className="cursor-pointer">Частично есть</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="no" id="wires-no" />
                  <Label htmlFor="wires-no" className="cursor-pointer">Нет, нужна прокладка</Label>
                </div>
              </RadioGroup>
            </div>
          </>
        )}

        {scenario && (
          <div className="pt-6 border-t">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold">Примерная стоимость:</span>
              <span className="text-2xl font-bold text-primary">{calculateEstimate().toLocaleString('ru-RU')} ₽</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              * Точная стоимость рассчитывается после осмотра объекта
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
