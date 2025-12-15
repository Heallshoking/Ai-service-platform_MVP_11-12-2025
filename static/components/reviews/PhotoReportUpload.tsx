import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';
import { useReviews } from '@/contexts/ReviewContext';
import { useAuth } from '@/contexts/AuthContext';

interface PhotoReportUploadProps {
  order: Order;
  onClose: () => void;
}

export default function PhotoReportUpload({ order, onClose }: PhotoReportUploadProps) {
  const { addPhotoReport } = useReviews();
  const { user } = useAuth();
  const [photos, setPhotos] = useState<Array<{ url: string; caption: string }>>([]);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setPhotos(prev => [
            ...prev,
            {
              url: event.target!.result as string,
              caption: ''
            }
          ]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const updateCaption = (index: number, caption: string) => {
    setPhotos(prev =>
      prev.map((photo, i) => (i === index ? { ...photo, caption } : photo))
    );
  };

  const removePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    if (photos.length === 0) return;

    addPhotoReport({
      orderId: order.id,
      uploadedBy: user?.phone || 'anonymous',
      uploaderRole: user?.role === 'electrician' ? 'electrician' : 'customer',
      photos: photos.map(p => ({
        url: p.url,
        caption: p.caption,
        timestamp: Date.now()
      }))
    });

    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Фотоотчёт</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <Icon name="X" size={20} />
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold mb-2">Заявка #{order.id.slice(-6)}</p>
            <p className="text-sm text-gray-600">Загрузите фотографии выполненных работ</p>
          </div>

          {photos.length > 0 && (
            <div className="space-y-4">
              {photos.map((photo, index) => (
                <Card key={index} className="p-4">
                  <div className="flex gap-4">
                    <img
                      src={photo.url}
                      alt={`Фото ${index + 1}`}
                      className="w-32 h-32 object-cover rounded-lg flex-shrink-0"
                    />
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold">Фото {index + 1}</p>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removePhoto(index)}
                        >
                          <Icon name="Trash2" size={16} className="text-red-500" />
                        </Button>
                      </div>
                      <Input
                        placeholder="Описание фото (необязательно)"
                        value={photo.caption}
                        onChange={(e) => updateCaption(index, e.target.value)}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          <label className="flex flex-col items-center justify-center gap-3 p-8 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-primary transition-colors">
            <Icon name="Camera" size={48} className="text-gray-400" />
            <div className="text-center">
              <p className="text-sm font-semibold text-gray-700">Добавить фотографии</p>
              <p className="text-xs text-gray-500 mt-1">Нажмите или перетащите файлы</p>
            </div>
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handlePhotoUpload}
            />
          </label>

          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} className="flex-1">
              Отмена
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={photos.length === 0}
              className="flex-1"
            >
              <Icon name="Upload" size={18} className="mr-2" />
              Загрузить ({photos.length})
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
