import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface CheckoutCommentsFormProps {
  formData: {
    comments: string;
    projectFiles: File[];
  };
  onFormDataChange: (data: Partial<{ comments: string; projectFiles: File[] }>) => void;
}

export default function CheckoutCommentsForm({ formData, onFormDataChange }: CheckoutCommentsFormProps) {
  return (
    <Card className="p-6 animate-fadeIn">
      <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
        <Icon name="MessageSquare" size={20} className="text-primary" />
        Остались пожелания к заявке?
      </h2>
      
      <div className="space-y-4">
        <div>
          <label className="text-sm text-gray-600 mb-2 block">
            Подробно опишите суть и особенности задачи: крайние сроки завершения работ, особенности подъезда автомобиля для разгрузки инструмента, наличие подведенных коммуникаций, наличие проекта и тд.
          </label>
          <textarea
            placeholder="Например: нужен подъём на 5 этаж, лифта нет. Работы желательно до 15 числа..."
            value={formData.comments}
            onChange={(e) => onFormDataChange({ comments: e.target.value })}
            className="w-full p-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all min-h-[100px]"
            rows={4}
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">
            Прикрепить проект (если есть)
          </label>
          <input
            type="file"
            multiple
            accept="image/*,.pdf,.dwg,.dxf"
            onChange={(e) => {
              const files = Array.from(e.target.files || []);
              onFormDataChange({ projectFiles: files });
            }}
            className="w-full p-2 border-2 border-gray-300 rounded-lg text-sm"
          />
          {formData.projectFiles.length > 0 && (
            <div className="mt-2 space-y-1">
              {formData.projectFiles.map((file, idx) => (
                <p key={idx} className="text-xs text-green-600 flex items-center gap-1">
                  <Icon name="FileCheck" size={14} />
                  {file.name}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
