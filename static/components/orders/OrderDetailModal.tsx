import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Order, ElectricalItem, calculateExecutorEarnings as calcEarnings } from '@/types/electrical';
import OrderStatusManager from './OrderStatusManager';
import AssignExecutorSelector from './AssignExecutorSelector';
import PaymentManager from '@/components/payments/PaymentManager';
import GoogleIntegrationPanel from '@/components/google/GoogleIntegrationPanel';
import OrderProgressSection from './OrderProgressSection';
import OrderInfoSection from './OrderInfoSection';
import OrderItemsSection from './OrderItemsSection';
import OrderContactSection from './OrderContactSection';
import OrderInfoCompactSection from './OrderInfoCompactSection';
import OrderReviewSection from './OrderReviewSection';
import OrderEarningsCard from '@/components/executor/OrderEarningsCard';
import OrderCompletionModal from './OrderCompletionModal';
import { useAuth } from '@/contexts/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import { useReviews } from '@/contexts/ReviewContext';
import { useCart } from '@/contexts/CartContext';

interface OrderDetailModalProps {
  order: Order;
  onClose: () => void;
  onStatusChange: (orderId: string, newStatus: Order['status']) => void;
  onRepeatOrder: (order: Order) => void;
  onAssignExecutor?: (orderId: string, electricianId: string, electricianName: string) => void;
}

const STATUS_LABELS = {
  'pending': 'Поиск мастера',
  'confirmed': 'Подтверждена',
  'on-the-way': 'В пути',
  'arrived': 'Мастер прибыл',
  'in-progress': 'В работе',
  'completed': 'Завершена'
};

const STATUS_COLORS = {
  'pending': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'confirmed': 'bg-blue-100 text-blue-800 border-blue-300',
  'on-the-way': 'bg-purple-100 text-purple-800 border-purple-300',
  'arrived': 'bg-indigo-100 text-indigo-800 border-indigo-300',
  'in-progress': 'bg-orange-100 text-orange-800 border-orange-300',
  'completed': 'bg-green-100 text-green-800 border-green-300'
};

export default function OrderDetailModal({ order, onClose, onStatusChange, onRepeatOrder, onAssignExecutor }: OrderDetailModalProps) {
  const { isAuthenticated, getExecutorProfile } = useAuth();
  const permissions = usePermissions();
  const { getOrderReviews, getOrderPhotoReports } = useReviews();
  const { addPayment, updatePaymentStatus } = useCart();
  const executorProfile = getExecutorProfile();
  const earnings = executorProfile ? calcEarnings(order, executorProfile) : null;
  const [isEditing, setIsEditing] = useState(false);
  const [editedOrder, setEditedOrder] = useState<Order>(order);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    info: false,
    items: false,
    contact: false,
    payment: false,
    review: false
  });
  
  const orderReviews = getOrderReviews(order.id);
  const orderPhotoReports = getOrderPhotoReports(order.id);
  const canLeaveReview = order.status === 'completed' && orderReviews.length === 0;

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const handleSaveEdit = () => {
    console.log('Сохранение изменений:', editedOrder);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedOrder(order);
    setIsEditing(false);
  };

  const handleOrderEdit = (field: keyof Order, value: string) => {
    setEditedOrder({
      ...editedOrder,
      [field]: value
    });
  };

  const handleItemEdit = (index: number, field: keyof ElectricalItem, value: string | number) => {
    const newItems = [...editedOrder.items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    const newTotalAmount = newItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
    
    setEditedOrder({
      ...editedOrder,
      items: newItems,
      totalAmount: newTotalAmount
    });
  };

  const { user } = useAuth();

  const handleAcceptOrder = () => {
    if (order.status === 'pending') {
      onStatusChange(order.id, 'confirmed');
      
      if (user && onAssignExecutor) {
        onAssignExecutor(order.id, user.uid, user.displayName || user.email || 'Мастер');
      }
    }
  };

  const handleStatusChange = (newStatus: Order['status']) => {
    if (newStatus === 'completed' && permissions.isAdmin && order.assignedTo && executorProfile) {
      setShowCompletionModal(true);
    } else {
      onStatusChange(order.id, newStatus);
    }
  };

  const handleConfirmCompletion = (notes?: string) => {
    console.log('Admin confirmed completion with notes:', notes);
    onStatusChange(order.id, 'completed');
    setShowCompletionModal(false);
  };

  const getNextStatus = (): Order['status'] | null => {
    switch (order.status) {
      case 'confirmed': return 'in-progress';
      case 'in-progress': return 'completed';
      default: return null;
    }
  };

  const getStatusActionLabel = (status: Order['status']): string => {
    switch (status) {
      case 'confirmed': return 'Начать работу';
      case 'in-progress': return 'Завершить';
      default: return 'Перевести';
    }
  };

  const nextStatus = getNextStatus();
  const currentOrder = isEditing ? editedOrder : order;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={onClose}>
              <Icon name="X" size={24} />
            </Button>
            <h2 className="text-xl font-bold">Заявка #{currentOrder.id.slice(-6)}</h2>
          </div>
          <div className="flex gap-2">
            {isAuthenticated && permissions.isAdmin && (
              <>
                {!isEditing ? (
                  <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                    <Icon name="Edit" size={16} className="mr-2" />
                    Редактировать
                  </Button>
                ) : (
                  <>
                    <Button variant="outline" size="sm" onClick={handleCancelEdit}>
                      Отмена
                    </Button>
                    <Button size="sm" onClick={handleSaveEdit}>
                      <Icon name="Save" size={16} className="mr-2" />
                      Сохранить
                    </Button>
                  </>
                )}
              </>
            )}
          </div>
        </div>

        <div className="p-6 space-y-4">
          {!isEditing ? (
            <Card className="p-4 bg-gray-50">
              <OrderInfoCompactSection 
                order={currentOrder}
                isElectrician={permissions.isElectrician}
              />
            </Card>
          ) : (
            <Card className="p-4 bg-gray-50">
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Детали заявки</h4>
                  <OrderInfoSection 
                    order={currentOrder} 
                    isEditing={isEditing}
                    onEdit={handleOrderEdit}
                    isAdmin={permissions.isAdmin}
                  />
                </div>
                <div className="border-t border-gray-200 pt-3">
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Контактные данные</h4>
                  <OrderContactSection 
                    order={currentOrder}
                    isEditing={isEditing}
                    onEdit={handleOrderEdit}
                    isElectrician={permissions.isElectrician}
                  />
                </div>
              </div>
            </Card>
          )}

          <OrderProgressSection order={currentOrder} isElectrician={permissions.isElectrician} />

          {permissions.isElectrician && user && currentOrder.assignedTo === user.uid && (
            <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
              {earnings && <OrderEarningsCard earnings={earnings} isPro={executorProfile?.isPro} />}
            </Card>
          )}

          {isAuthenticated && permissions.canEditOrders && (
            <>
              {order.status === 'pending' && (
                <Button 
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
                  size="lg"
                  onClick={handleAcceptOrder}
                >
                  <Icon name="UserPlus" size={20} className="mr-2" />
                  {permissions.isElectrician && !permissions.isAdmin ? 'Откликнуться' : 'Принять заявку'}
                </Button>
              )}
            </>
          )}

          {permissions.isElectrician && user && currentOrder.assignedTo === user.uid && (
            <OrderStatusManager 
              order={currentOrder} 
              onStatusChange={handleStatusChange}
            />
          )}

          {permissions.isAdmin && (
            <OrderStatusManager 
              order={currentOrder} 
              onStatusChange={handleStatusChange}
            />
          )}

          {isAuthenticated && permissions.isAdmin && order.status !== 'pending' && onAssignExecutor && (
            <Card className="p-4">
              <AssignExecutorSelector
                order={currentOrder}
                onAssign={onAssignExecutor}
              />
            </Card>
          )}

          {isAuthenticated && permissions.isAdmin && (
            <Card className="p-4">
              <GoogleIntegrationPanel order={currentOrder} />
            </Card>
          )}

          <Card className="p-4">
            <button
              onClick={() => toggleSection('items')}
              className="w-full flex items-center justify-between"
            >
              <h3 className="font-semibold flex items-center gap-2">
                <Icon name="ShoppingCart" size={18} />
                Состав заявки
              </h3>
              <Icon name={expandedSections.items ? 'ChevronUp' : 'ChevronDown'} size={20} />
            </button>
            {expandedSections.items && (
              <div className="mt-4">
                <OrderItemsSection 
                  items={currentOrder.items}
                  totalAmount={currentOrder.totalAmount}
                  isEditing={isEditing}
                  onItemEdit={handleItemEdit}
                />
              </div>
            )}
          </Card>

          {permissions.canEditOrders && (
            <Card className="p-4">
              <PaymentManager
                order={currentOrder}
                onAddPayment={addPayment}
                onUpdatePaymentStatus={updatePaymentStatus}
              />
            </Card>
          )}



          <Card className="p-4">
            <button
              onClick={() => toggleSection('review')}
              className="w-full flex items-center justify-between"
            >
              <h3 className="font-semibold flex items-center gap-2">
                <Icon name="Star" size={18} />
                Отзывы и фото
              </h3>
              <Icon name={expandedSections.review ? 'ChevronUp' : 'ChevronDown'} size={20} />
            </button>
            {expandedSections.review && (
              <div className="mt-4">
                <OrderReviewSection
                  order={currentOrder}
                  canLeaveReview={canLeaveReview}
                  orderReviews={orderReviews}
                  orderPhotoReports={orderPhotoReports}
                  isAuthenticated={isAuthenticated}
                  canManageReviews={permissions.canManageReviews}
                />
              </div>
            )}
          </Card>

          <div className="flex gap-3 pt-4">
            <Button 
              variant="outline" 
              className="flex-1"
              onClick={onClose}
            >
              Закрыть
            </Button>
            
            {order.status === 'completed' && (
              <Button 
                className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
                onClick={() => {
                  onRepeatOrder(order);
                  onClose();
                }}
              >
                <Icon name="Repeat" size={18} className="mr-2" />
                Повторить заявку
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Модальное окно подтверждения завершения */}
      {showCompletionModal && executorProfile && (
        <OrderCompletionModal
          order={order}
          executorProfile={executorProfile}
          onConfirm={handleConfirmCompletion}
          onCancel={() => setShowCompletionModal(false)}
        />
      )}
    </div>
  );
}