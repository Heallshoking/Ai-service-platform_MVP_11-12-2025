import Icon from './ui/icon';

interface OrderProgressBarProps {
  currentStatus: 'planning' | 'scheduled' | 'in_progress' | 'completed';
}

const OrderProgressBar = ({ currentStatus }: OrderProgressBarProps) => {
  const steps = [
    { key: 'planning', icon: 'Check', label: 'Планирование' },
    { key: 'scheduled', icon: 'Calendar', label: 'Встреча назначена' },
    { key: 'in_progress', icon: 'Wrench', label: 'В работе' },
    { key: 'completed', icon: 'CheckCircle2', label: 'Завершено' }
  ];

  const statusIndex = steps.findIndex(s => s.key === currentStatus);

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between relative">
        {steps.map((step, index) => {
          const isActive = index <= statusIndex;
          const isCompleted = index < statusIndex;
          
          return (
            <div key={step.key} className="flex flex-col items-center relative z-10">
              <div 
                className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
                  isActive 
                    ? 'bg-primary text-primary-foreground border-4 border-orange-300' 
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                <Icon name={step.icon as any} size={24} />
              </div>
              <p className={`text-xs mt-2 text-center max-w-[80px] ${
                isActive ? 'text-foreground font-medium' : 'text-muted-foreground'
              }`}>
                {step.label}
              </p>
              
              {index < steps.length - 1 && (
                <div 
                  className={`absolute top-7 left-[50%] w-[calc(100vw/4)] h-1 -z-10 transition-all ${
                    isCompleted ? 'bg-primary' : 'bg-muted'
                  }`}
                  style={{ transform: 'translateX(0)' }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrderProgressBar;