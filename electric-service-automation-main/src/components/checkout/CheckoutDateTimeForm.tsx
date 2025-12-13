import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface CheckoutDateTimeFormProps {
  formData: {
    date: string;
    time: string;
  };
  errors: {
    date: string;
    time: string;
  };
  onFormDataChange: (data: Partial<{ date: string; time: string }>) => void;
}

export default function CheckoutDateTimeForm({ formData, errors, onFormDataChange }: CheckoutDateTimeFormProps) {
  return (
    <Card className="p-6 animate-fadeIn">
      <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
        <Icon name="Calendar" size={20} className="text-primary" />
        Дата и время
      </h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-2 block">
            Дата <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={formData.date}
            onChange={(e) => onFormDataChange({ date: e.target.value })}
            min={new Date().toISOString().split('T')[0]}
            className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
              errors.date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.date && (
            <p className="text-xs text-red-500 mt-1">{errors.date}</p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium mb-2 block">
            Время <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.time}
            onChange={(e) => onFormDataChange({ time: e.target.value })}
            className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
              errors.time ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Выберите</option>
            <option value="09:00">09:00</option>
            <option value="10:00">10:00</option>
            <option value="11:00">11:00</option>
            <option value="12:00">12:00</option>
            <option value="13:00">13:00</option>
            <option value="14:00">14:00</option>
            <option value="15:00">15:00</option>
            <option value="16:00">16:00</option>
            <option value="17:00">17:00</option>
            <option value="18:00">18:00</option>
          </select>
          {errors.time && (
            <p className="text-xs text-red-500 mt-1">{errors.time}</p>
          )}
        </div>
      </div>
    </Card>
  );
}
