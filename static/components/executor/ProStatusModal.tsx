import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Icon from '@/components/ui/icon';

type ProStatusType = 'education' | 'car' | 'tools';

interface ProStatusModalProps {
  type: ProStatusType;
  onClose: () => void;
  onSubmit: (file: File) => void;
  isVerified?: boolean;
}

const MODAL_CONTENT = {
  education: {
    title: 'Добавить образование',
    icon: 'GraduationCap',
    color: 'purple',
    benefits: [
      '💰 +10% к доходу за каждый заказ',
      '📜 Повышение доверия клиентов',
      '⭐ Приоритет в списке мастеров'
    ],
    conditions: [
      'Диплом специалиста по электромонтажным работам',
      'Свидетельство о профессиональной подготовке',
      'Удостоверение о повышении квалификации',
      'Справка с места работы (для опытных мастеров)'
    ],
    fileHint: 'Загрузите фото диплома или сертификата (JPG, PNG или PDF)'
  },
  car: {
    title: 'Автомобиль',
    icon: 'Car',
    color: 'blue',
    benefits: [
      '🚗 +10% больше заказов от клиентов',
      '⚡ Быстрый выезд к клиенту',
      '📦 Возможность перевозки материалов',
      '🌍 Работа в разных районах города'
    ],
    conditions: [
      'Личный автомобиль в исправном состоянии',
      'Действующее водительское удостоверение',
      'Возможность оперативного выезда',
      'Наличие базового набора инструментов в авто'
    ],
    fileHint: 'Загрузите фото автомобиля и/или водительского удостоверения'
  },
  tools: {
    title: 'Инструменты',
    icon: 'Wrench',
    color: 'orange',
    benefits: [
      '🔧 +10% к доверию и рейтингу',
      '⚡ Больше сложных и дорогих заказов',
      '💼 Профессиональный статус',
      '🎯 Работа без ограничений'
    ],
    conditions: [
      'Мультиметр для диагностики',
      'Набор отверток и ключей',
      'Перфоратор или дрель',
      'Инструмент для зачистки проводов',
      'Изолента, кабель-каналы и расходники'
    ],
    fileHint: 'Загрузите фото вашего набора инструментов'
  }
};

export default function ProStatusModal({ type, onClose, onSubmit, isVerified }: ProStatusModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const content = MODAL_CONTENT[type];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onSubmit(selectedFile);
      onClose();
    }
  };

  const colorClasses = {
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-700',
      button: 'bg-purple-600 hover:bg-purple-700',
      icon: 'text-purple-600'
    },
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      button: 'bg-blue-600 hover:bg-blue-700',
      icon: 'text-blue-600'
    },
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      text: 'text-orange-700',
      button: 'bg-orange-600 hover:bg-orange-700',
      icon: 'text-orange-600'
    }
  };

  const colors = colorClasses[content.color];

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${colors.bg}`}>
              <Icon name={content.icon as any} className={`h-6 w-6 ${colors.icon}`} />
            </div>
            <h2 className="text-xl font-bold">{content.title}</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <Icon name="X" size={24} />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {isVerified ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-700">
                <Icon name="CheckCircle" className="h-5 w-5" />
                <p className="font-semibold">Статус уже подтвержден администратором</p>
              </div>
            </div>
          ) : (
            <>
              <div className={`${colors.bg} border ${colors.border} rounded-lg p-4`}>
                <h3 className={`font-semibold mb-2 ${colors.text}`}>Преимущества:</h3>
                <ul className="space-y-1">
                  {content.benefits.map((benefit, index) => (
                    <li key={index} className="text-sm text-gray-700">{benefit}</li>
                  ))}
                </ul>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold text-gray-900">Условия для подтверждения:</h3>
                <ul className="space-y-1 list-disc list-inside">
                  {content.conditions.map((condition, index) => (
                    <li key={index} className="text-sm text-gray-600">{condition}</li>
                  ))}
                </ul>
              </div>

              <div className="space-y-3">
                <Label className="text-sm font-medium">{content.fileHint}</Label>
                <Input
                  type="file"
                  accept={type === 'education' ? 'image/*,.pdf' : 'image/*'}
                  onChange={handleFileChange}
                  className="cursor-pointer"
                />
                {selectedFile && (
                  <p className="text-sm text-green-600 flex items-center gap-2">
                    <Icon name="CheckCircle" size={16} />
                    {selectedFile.name}
                  </p>
                )}
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs text-amber-800">
                  <Icon name="Info" size={14} className="inline mr-1" />
                  После загрузки файл будет отправлен на проверку администратору. Обычно это занимает 1-2 рабочих дня.
                </p>
              </div>
            </>
          )}

          <div className="flex gap-3 pt-4">
            <Button 
              variant="outline" 
              className="flex-1"
              onClick={onClose}
            >
              {isVerified ? 'Закрыть' : 'Отмена'}
            </Button>
            {!isVerified && (
              <Button 
                className={`flex-1 text-white ${colors.button}`}
                onClick={handleSubmit}
                disabled={!selectedFile}
              >
                <Icon name="Upload" size={18} className="mr-2" />
                Отправить на проверку
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
