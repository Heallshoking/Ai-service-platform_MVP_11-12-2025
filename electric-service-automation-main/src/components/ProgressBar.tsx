import { cn } from '@/lib/utils';
import { useState } from 'react';
import Icon from '@/components/ui/icon';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface Step {
  number: number;
  label: string;
  isActive: boolean;
  isCompleted: boolean;
}

interface ProgressBarProps {
  currentStep: number;
  steps: string[];
  className?: string;
  onStepClick?: (step: number) => void;
}

export default function ProgressBar({ currentStep, steps, className, onStepClick }: ProgressBarProps) {
  const [showContactDialog, setShowContactDialog] = useState(false);
  
  const stepsData: Step[] = steps.map((label, index) => ({
    number: index + 1,
    label,
    isActive: index + 1 === currentStep,
    isCompleted: index + 1 < currentStep
  }));

  return (
    <>
    <TooltipProvider>
    <div className={cn('w-full py-4', className)}>
      <div className="flex items-center justify-between relative gap-3">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => setShowContactDialog(true)}
              className="relative flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-600 hover:via-teal-600 hover:to-cyan-600 flex items-center justify-center shadow-xl hover:shadow-2xl transition-all hover:scale-105 group overflow-hidden"
            >
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity" />
              <Icon name="Phone" size={22} className="text-white group-hover:animate-wiggle relative z-10" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="bg-gray-900 text-white border-0">
            <p className="font-medium">Связаться с нами</p>
          </TooltipContent>
        </Tooltip>
        
        <div className="flex items-center justify-between flex-1 relative">
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-gray-200 -z-10">
          <div 
            className="h-full bg-primary transition-all duration-500"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
          />
        </div>

          {stepsData.map((step, index) => {
            const canNavigate = step.isCompleted || step.isActive;
            const tooltipText = !canNavigate 
              ? `Сначала завершите шаг "${steps[currentStep - 1]}"`
              : step.label;
            
            return (
              <Tooltip key={index}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => canNavigate && onStepClick?.(step.number)}
                    disabled={!canNavigate || !onStepClick}
                    className="flex flex-col items-center flex-1 disabled:cursor-not-allowed"
                  >
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 mb-2',
                        step.isCompleted && 'bg-primary text-white shadow-md',
                        step.isActive && 'bg-primary text-white shadow-lg ring-4 ring-primary/20 scale-110',
                        !step.isCompleted && !step.isActive && 'bg-gray-200 text-gray-400',
                        canNavigate && onStepClick && 'cursor-pointer hover:scale-105'
                      )}
                    >
                      {step.isCompleted ? '✓' : step.number}
                    </div>
                    <span 
                      className={cn(
                        'text-xs text-center transition-colors duration-300',
                        (step.isActive || step.isCompleted) ? 'text-primary font-semibold' : 'text-gray-400'
                      )}
                    >
                      {step.label}
                    </span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="bg-gray-900 text-white border-0">
                  <p>{tooltipText}</p>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </div>
    </div>
    </TooltipProvider>
    
    <Dialog open={showContactDialog} onOpenChange={setShowContactDialog}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-xl">Связаться с нами</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-4">
          <a
            href="tel:+74012520725"
            className="flex items-center gap-4 p-4 rounded-lg border-2 hover:border-primary transition-all hover:shadow-md"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <Icon name="Phone" size={24} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">Телефон</div>
              <div className="text-sm text-muted-foreground">+7 (4012) 52-07-25</div>
            </div>
          </a>
          
          <a
            href="https://wa.me/74012520725"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 rounded-lg border-2 hover:border-primary transition-all hover:shadow-md"
          >
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Icon name="MessageCircle" size={24} className="text-green-600" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">WhatsApp</div>
              <div className="text-sm text-muted-foreground">+7 (4012) 52-07-25</div>
            </div>
          </a>
          
          <a
            href="https://t.me/konigelectric"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 rounded-lg border-2 hover:border-primary transition-all hover:shadow-md"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <Icon name="Send" size={24} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">Telegram</div>
              <div className="text-sm text-muted-foreground">@konigelectric</div>
            </div>
          </a>
          
          <a
            href="https://vk.com/electro_konig"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 rounded-lg border-2 hover:border-primary transition-all hover:shadow-md"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <Icon name="Globe" size={24} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">ВКонтакте</div>
              <div className="text-sm text-muted-foreground">electro_konig</div>
            </div>
          </a>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
}