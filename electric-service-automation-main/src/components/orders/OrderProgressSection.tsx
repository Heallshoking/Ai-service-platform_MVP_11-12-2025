import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Order } from '@/types/electrical';

interface OrderProgressSectionProps {
  order: Order;
  isElectrician?: boolean;
}

const getProgressData = (status: Order['status'], hasAssignedExecutor: boolean) => {
  const steps = [
    {
      key: 'step1',
      icon: hasAssignedExecutor ? 'CheckCircle' : 'Search',
      label: hasAssignedExecutor ? 'Заявка подтверждена' : 'Поиск мастера',
      progress: 20
    },
    {
      key: 'step2',
      icon: 'Navigation',
      label: 'В пути',
      progress: 40
    },
    {
      key: 'step3',
      icon: 'MapPin',
      label: 'Мастер прибыл',
      progress: 60
    },
    {
      key: 'step4',
      icon: 'Wrench',
      label: 'Работа в процессе',
      progress: 80
    },
    {
      key: 'step5',
      icon: 'Award',
      label: 'Работа завершена',
      progress: 100
    }
  ];

  let currentProgress = 0;
  switch (status) {
    case 'pending':
      currentProgress = hasAssignedExecutor ? 20 : 10;
      break;
    case 'confirmed':
      currentProgress = 20;
      break;
    case 'on-the-way':
      currentProgress = 40;
      break;
    case 'arrived':
      currentProgress = 60;
      break;
    case 'in-progress':
      currentProgress = 80;
      break;
    case 'completed':
      currentProgress = 100;
      break;
  }

  return { steps, currentProgress };
};

export default function OrderProgressSection({ order, isElectrician = false }: OrderProgressSectionProps) {
  const hasAssignedExecutor = !!order.assignedTo;
  const { steps, currentProgress } = getProgressData(order.status, hasAssignedExecutor);

  const getStepStatus = (stepProgress: number) => {
    if (currentProgress >= stepProgress) return 'completed';
    if (currentProgress >= stepProgress - 10) return 'current';
    return 'pending';
  };

  return (
    <Card className="p-6 animate-fadeIn">
      <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
        <Icon name="Activity" size={20} className="text-primary" />
        Статус выполнения
      </h2>
      
      <div className="relative pt-1 mb-6">
        <div className="flex mb-2 items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-gray-700">
              {steps.find(s => getStepStatus(s.progress) === 'current' || getStepStatus(s.progress) === 'completed')?.label || steps[0].label}
            </span>
          </div>
          <div className="text-right">
            <span className="text-xs font-semibold inline-block text-primary">
              {currentProgress}%
            </span>
          </div>
        </div>
        <div className="overflow-hidden h-3 mb-4 text-xs flex rounded-full bg-gray-200">
          <div 
            style={{ width: `${currentProgress}%` }} 
            className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 rounded-full"
          />
        </div>
      </div>

      <div className="space-y-3">
        {steps.map((step) => {
          const stepStatus = getStepStatus(step.progress);
          const isCompleted = stepStatus === 'completed';
          const isCurrent = stepStatus === 'current';
          
          return (
            <div key={step.key} className="flex items-center gap-3 text-sm">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                isCompleted 
                  ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg' 
                  : isCurrent
                  ? 'bg-blue-100 text-blue-600 border-2 border-blue-400'
                  : 'bg-gray-200 text-gray-400'
              }`}>
                <Icon name={step.icon as any} size={18} />
              </div>
              <span className={
                isCompleted 
                  ? 'font-semibold text-gray-800' 
                  : isCurrent
                  ? 'font-medium text-blue-700'
                  : 'text-muted-foreground'
              }>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {order.status === 'on-the-way' && !isElectrician && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-blue-800">
            <Icon name="Clock" size={16} />
            <span className="font-medium">Ориентировочное время прибытия: ~40–60 минут</span>
          </div>
        </div>
      )}
    </Card>
  );
}
