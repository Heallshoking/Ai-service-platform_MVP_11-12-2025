import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import ReviewForm from '@/components/reviews/ReviewForm';
import ReviewList from '@/components/reviews/ReviewList';
import PhotoReportUpload from '@/components/reviews/PhotoReportUpload';
import { Order } from '@/types/electrical';
import { Review, PhotoReport } from '@/types/review';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface OrderReviewSectionProps {
  order: Order;
  canLeaveReview: boolean;
  orderReviews: Review[];
  orderPhotoReports: PhotoReport[];
  isAuthenticated: boolean;
  canManageReviews: boolean;
}

export default function OrderReviewSection({ 
  order, 
  canLeaveReview, 
  orderReviews, 
  orderPhotoReports,
  isAuthenticated,
  canManageReviews
}: OrderReviewSectionProps) {
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [showPhotoUpload, setShowPhotoUpload] = useState(false);

  return (
    <>
      {canLeaveReview && (
        <Card className="p-6 animate-fadeIn bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center flex-shrink-0 shadow-lg">
              <Icon name="Star" size={24} className="text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-lg mb-2 text-gray-800">Оставьте отзыв о работе</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Ваше мнение поможет нам улучшить качество обслуживания
              </p>
              <Button 
                onClick={() => setShowReviewForm(true)}
                className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 shadow-md"
              >
                <Icon name="MessageSquare" size={16} className="mr-2" />
                Написать отзыв
              </Button>
            </div>
          </div>
        </Card>
      )}

      {showReviewForm && (
        <ReviewForm
          orderId={order.id}
          onClose={() => setShowReviewForm(false)}
        />
      )}

      <div>
        {orderReviews.length > 0 ? (
          <ReviewList reviews={orderReviews} />
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <Icon name="MessageSquare" size={32} className="text-gray-400" />
            </div>
            <p className="text-gray-500 mb-4">Пока нет отзывов</p>
            {canManageReviews && order.status === 'completed' && (
              <Button 
                variant="outline"
                onClick={() => {
                  const phone = order.customerPhone || order.phone;
                  const message = `Здравствуйте! Спасибо за заказ #${order.id.slice(-6)}. Будем рады, если вы оставите отзыв о нашей работе.`;
                  window.open(`https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`, '_blank');
                }}
              >
                <Icon name="Send" size={16} className="mr-2" />
                Запросить отзыв
              </Button>
            )}
          </div>
        )}
      </div>

      {isAuthenticated && canManageReviews && (
        <Card className="p-6 animate-fadeIn">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="photo-reports">
              <AccordionTrigger className="text-lg font-bold">
                <div className="flex items-center gap-2">
                  <Icon name="Camera" size={20} className="text-primary" />
                  Фотоотчёты {orderPhotoReports.length > 0 && `(${orderPhotoReports.length})`}
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-4">
                  <Button 
                    onClick={() => setShowPhotoUpload(true)}
                    variant="outline"
                    className="w-full"
                  >
                    <Icon name="Upload" size={16} className="mr-2" />
                    Загрузить фотоотчёт
                  </Button>
                  
                  {orderPhotoReports.length > 0 ? (
                    <div className="grid grid-cols-2 gap-4">
                      {orderPhotoReports.map((report) => (
                        <div key={report.id} className="border rounded-lg overflow-hidden">
                          <img 
                            src={report.photoUrl} 
                            alt={report.description || 'Фотоотчёт'} 
                            className="w-full h-48 object-cover"
                          />
                          {report.description && (
                            <div className="p-2 bg-gray-50 text-sm">
                              {report.description}
                            </div>
                          )}
                          <div className="p-2 bg-gray-100 text-xs text-muted-foreground">
                            {new Date(report.createdAt).toLocaleString('ru-RU')}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Icon name="ImageOff" size={32} className="mx-auto mb-2 text-gray-400" />
                      <p>Фотоотчёты ещё не загружены</p>
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>
      )}

      {showPhotoUpload && (
        <PhotoReportUpload
          orderId={order.id}
          onClose={() => setShowPhotoUpload(false)}
        />
      )}
    </>
  );
}