import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';
import { Review } from '@/types/review';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import { useReviews } from '@/contexts/ReviewContext';

interface ReviewListProps {
  reviews: Review[];
  showOrderId?: boolean;
}

export default function ReviewList({ reviews, showOrderId = false }: ReviewListProps) {
  const { isAuthenticated } = useAuth();
  const permissions = usePermissions();
  const { addReviewResponse } = useReviews();
  const [respondingTo, setRespondingTo] = useState<string | null>(null);
  const [responseText, setResponseText] = useState('');
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Icon
            key={star}
            name="Star"
            size={16}
            className={star <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}
          />
        ))}
      </div>
    );
  };

  const handleSubmitResponse = (reviewId: string) => {
    if (!responseText.trim()) return;

    addReviewResponse(reviewId, responseText);
    setRespondingTo(null);
    setResponseText('');
  };

  if (reviews.length === 0) {
    return (
      <Card className="p-8 text-center">
        <Icon name="MessageSquare" size={48} className="mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600">Отзывов пока нет</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <Card key={review.id} className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-full flex items-center justify-center font-bold">
                  {review.customerName[0].toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold">{review.customerName}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(review.createdAt).toLocaleDateString('ru-RU', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </div>
            </div>
            {renderStars(review.rating)}
          </div>

          {showOrderId && (
            <p className="text-sm text-gray-600 mb-2">
              Заявка #{review.orderId.slice(-6)}
            </p>
          )}

          {review.comment && (
            <p className="text-gray-700 mb-4">{review.comment}</p>
          )}

          {review.photos.length > 0 && (
            <div className="grid grid-cols-4 gap-2 mb-4">
              {review.photos.map((photo, index) => (
                <img
                  key={index}
                  src={photo}
                  alt={`Фото ${index + 1}`}
                  className="w-full h-24 object-cover rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setSelectedPhoto(photo)}
                />
              ))}
            </div>
          )}

          {review.response && (
            <div className="bg-gray-50 rounded-lg p-4 mt-4">
              <p className="text-sm font-semibold text-gray-700 mb-2">
                Ответ от {review.electricianName || 'Мастера'}
              </p>
              <p className="text-sm text-gray-600">{review.response.text}</p>
              <p className="text-xs text-gray-400 mt-2">
                {new Date(review.response.createdAt).toLocaleDateString('ru-RU')}
              </p>
            </div>
          )}

          {isAuthenticated && permissions.canEditOrders && !review.response && (
            <div className="mt-4">
              {respondingTo === review.id ? (
                <div className="space-y-2">
                  <Textarea
                    placeholder="Ваш ответ на отзыв..."
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleSubmitResponse(review.id)}
                      disabled={!responseText.trim()}
                    >
                      Отправить
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setRespondingTo(null);
                        setResponseText('');
                      }}
                    >
                      Отмена
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setRespondingTo(review.id)}
                >
                  <Icon name="MessageCircle" size={16} className="mr-2" />
                  Ответить
                </Button>
              )}
            </div>
          )}
        </Card>
      ))}

      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPhoto(null)}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 text-white"
            onClick={() => setSelectedPhoto(null)}
          >
            <Icon name="X" size={24} />
          </Button>
          <img
            src={selectedPhoto}
            alt="Увеличенное фото"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  );
}
