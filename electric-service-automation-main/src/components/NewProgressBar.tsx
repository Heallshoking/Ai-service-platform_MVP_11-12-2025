import { useState } from 'react';
import Icon from '@/components/ui/icon';
import { cn } from '@/lib/utils';

interface ProgressStep {
  id: number;
  label: string;
  icon: string;
  onClick?: () => void;
}

interface NewProgressBarProps {
  steps: ProgressStep[];
  currentStep: number;
  hasItems: boolean;
  cartConfirmed: boolean;
}

export default function NewProgressBar({ steps, currentStep, hasItems, cartConfirmed }: NewProgressBarProps) {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);

  const getStepStatus = (stepId: number) => {
    if (stepId === 1) {
      return hasItems ? 'half' : 'empty';
    }
    if (stepId === 2) {
      if (!hasItems) return 'disabled';
      return cartConfirmed ? 'full' : 'half';
    }
    if (stepId === 3) {
      if (!cartConfirmed) return 'disabled';
      return currentStep >= 3 ? 'half' : 'empty';
    }
    return 'empty';
  };

  const isClickable = (stepId: number) => {
    if (stepId === 1) return true;
    if (stepId === 2) return hasItems;
    if (stepId === 3) return cartConfirmed;
    return false;
  };

  const getTooltip = (stepId: number) => {
    if (stepId === 2 && !hasItems) {
      return 'Сначала добавьте услуги';
    }
    if (stepId === 3 && !cartConfirmed) {
      return 'Сначала подтвердите план работ';
    }
    return null;
  };

  return (
    <div className="flex items-center justify-between gap-2 px-2">
      {steps.map((step, index) => {
        const status = getStepStatus(step.id);
        const clickable = isClickable(step.id);
        const tooltip = getTooltip(step.id);

        return (
          <div key={step.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1 gap-2">
              <div className="relative group">
                <button
                  onClick={() => clickable && step.onClick?.()}
                  disabled={!clickable}
                  onMouseEnter={() => setHoveredStep(step.id)}
                  onMouseLeave={() => setHoveredStep(null)}
                  className={cn(
                    "w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 relative overflow-hidden border-2",
                    clickable ? "cursor-pointer hover:scale-110" : "cursor-not-allowed opacity-50",
                    status === 'full' && "border-blue-500 bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg",
                    status === 'half' && "border-blue-400 bg-gradient-to-t from-blue-400 via-blue-200 to-blue-50 shadow-md",
                    status === 'empty' && "border-gray-300 bg-white",
                    status === 'disabled' && "border-gray-200 bg-gray-50"
                  )}
                >
                  <Icon 
                    name={step.icon as any} 
                    size={24} 
                    className={cn(
                      "transition-colors",
                      status === 'full' && "text-white",
                      status === 'half' && "text-blue-600",
                      (status === 'empty' || status === 'disabled') && "text-gray-400"
                    )}
                  />
                </button>
                
                {tooltip && hoveredStep === step.id && (
                  <div className="absolute -bottom-16 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-3 py-2 rounded-lg whitespace-nowrap z-10 shadow-xl">
                    {tooltip}
                    <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-800 rotate-45"></div>
                  </div>
                )}
              </div>
              
              <span className={cn(
                "text-xs font-medium text-center transition-colors",
                clickable ? "text-gray-700" : "text-gray-400"
              )}>
                {step.label}
              </span>
            </div>
            
            {index < steps.length - 1 && (
              <div className={cn(
                "h-1 flex-1 mx-2 rounded-full transition-colors",
                status === 'full' ? "bg-gradient-to-r from-blue-500 to-indigo-600" : "bg-gray-200"
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
}