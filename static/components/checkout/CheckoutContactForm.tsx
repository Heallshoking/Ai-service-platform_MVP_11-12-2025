import { IMaskInput } from 'react-imask';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface CheckoutContactFormProps {
  formData: {
    customerName: string;
    phone: string;
    address: string;
  };
  errors: {
    customerName: string;
    phone: string;
    address: string;
  };
  onFormDataChange: (data: Partial<{ customerName: string; phone: string; address: string }>) => void;
}

export default function CheckoutContactForm({ formData, errors, onFormDataChange }: CheckoutContactFormProps) {
  return (
    <Card className="p-6 animate-fadeIn">
      <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
        <Icon name="User" size={20} className="text-primary" />
        Контактные данные
      </h2>
      
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">
            Ваше имя <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="Как к вам обращаться"
            value={formData.customerName}
            onChange={(e) => onFormDataChange({ customerName: e.target.value })}
            className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
              errors.customerName ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.customerName && (
            <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
              <Icon name="AlertCircle" size={14} />
              {errors.customerName}
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">
            Номер телефона <span className="text-red-500">*</span>
          </label>
          <IMaskInput
            mask="8 (000) 000-00-00"
            value={formData.phone}
            onAccept={(value: string) => onFormDataChange({ phone: value })}
            placeholder="8 (___) ___-__-__"
            className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
              errors.phone ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.phone && (
            <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
              <Icon name="AlertCircle" size={14} />
              {errors.phone}
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">
            Адрес: (желательно)
          </label>
          <input
            type="text"
            placeholder="Улица, дом, квартира"
            value={formData.address}
            onChange={(e) => onFormDataChange({ address: e.target.value })}
            className={`w-full p-3 border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
              errors.address ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.address && (
            <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
              <Icon name="AlertCircle" size={14} />
              {errors.address}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}