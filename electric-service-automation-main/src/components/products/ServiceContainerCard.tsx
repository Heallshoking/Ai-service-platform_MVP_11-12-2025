import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Checkbox } from '@/components/ui/checkbox';
import { ServiceContainer, ServiceOption } from './types';
import { useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ServiceContainerCardProps {
  container: ServiceContainer;
  actualIndex: number;
  toggleContainer: (index: number) => void;
  toggleOption: (containerIndex: number, optionId: string) => void;
  updateOptionQuantity: (containerIndex: number, optionId: string, newQuantity: number) => void;
  updateVoltage: (containerIndex: number, optionId: string, voltage: '220V' | '380V') => void;
  calculateContainerTotal: (container: ServiceContainer) => number;
}

const iconMap: Record<string, string> = {
  'chandelier-1': 'Lightbulb',
  'sw-install': 'ToggleLeft',
  'out-install': 'Plug'
};

const iconColorMap: Record<string, { bg: string; icon: string }> = {
  'chandelier-1': { bg: 'from-amber-100 to-orange-100', icon: 'text-amber-600' },
  'sw-install': { bg: 'from-blue-100 to-cyan-100', icon: 'text-blue-600' },
  'out-install': { bg: 'from-green-100 to-emerald-100', icon: 'text-green-600' }
};

export default function ServiceContainerCard({
  container,
  actualIndex,
  toggleContainer,
  toggleOption,
  updateOptionQuantity,
  updateVoltage,
  calculateContainerTotal
}: ServiceContainerCardProps) {
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
    main: true,
    construction: false,
    panel: false
  });

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const isSingleOption = container.options.length === 1;
  const singleOption = isSingleOption ? container.options[0] : null;

  const calculateOptionPrice = (option: ServiceOption) => {
    if (option.customPrice) return 'По запросу';
    
    let price = option.price * option.quantity;
    
    if (option.discount && option.quantity >= option.discount.minQuantity) {
      price = price * (1 - option.discount.percent / 100);
    }
    
    return `${price.toLocaleString('ru-RU')} ₽`;
  };

  const getDiscountLabel = (option: ServiceOption) => {
    if (!option.discount) return null;
    return `Скидка ${option.discount.percent}% от ${option.discount.minQuantity} шт.`;
  };

  const getMinPrice = () => {
    const prices = container.options.filter(o => !o.customPrice).map(o => o.price);
    return prices.length > 0 ? Math.min(...prices) : 0;
  };

  const renderOption = (option: ServiceOption) => {
    const hasDiscount = option.discount && option.quantity >= option.discount.minQuantity;
    
    if (option.id === 'crystal') {
      return (
        <div key={option.id} className="p-3 rounded-lg bg-blue-50 border border-blue-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              <Icon name="Info" size={16} className="text-blue-500 flex-shrink-0" />
              <span className="text-xs text-gray-600">
                {option.name} — {option.price} ₽
              </span>
            </div>
          </div>
        </div>
      );
    }
    
    if (option.isInfo) {
      return (
        <div key={option.id} className="p-3 rounded-lg bg-blue-50 border border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              <Icon name="Info" size={16} className="text-blue-500 flex-shrink-0" />
              <span className="text-xs text-gray-700 font-medium">
                {option.name}
              </span>
            </div>
            {option.price > 0 && (
              <span className="text-sm font-bold text-blue-700 ml-2">
                +{option.price} ₽
              </span>
            )}
          </div>
        </div>
      );
    }
    
    return (
      <div 
        key={option.id}
        className={`p-3 rounded-lg transition-all ${
          option.enabled ? 'bg-green-100' : 'bg-white'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <Checkbox
              id={`${container.productId}-${option.id}`}
              checked={option.enabled}
              onCheckedChange={() => toggleOption(actualIndex, option.id)}
            />
            <label 
              htmlFor={`${container.productId}-${option.id}`}
              className="text-sm font-medium cursor-pointer flex-1"
            >
              <div className="flex items-center gap-2">
                <span>{option.name}</span>
                {option.description && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Icon name="Info" size={16} className="text-blue-500 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-xs">{option.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
                {option.unit && <span className="text-xs text-gray-500">({option.unit})</span>}
              </div>
              {option.customPrice && (
                <p className="text-xs text-blue-600 mt-1">
                  Полная замена старого вводного кабеля, либо наращивание существующего
                </p>
              )}
              {option.id === 'gas-sensor' && (
                <p className="text-xs text-blue-600 mt-1">
                  Газоанализаторы с перекладкой проводки
                </p>
              )}
            </label>
          </div>
          
          {option.enabled ? (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  updateOptionQuantity(actualIndex, option.id, option.quantity - 1);
                }}
                className="h-8 w-8 p-0 rounded-full bg-gray-200 hover:bg-gray-300"
              >
                <Icon name="Minus" size={16} />
              </Button>
              <span className="font-bold text-lg min-w-[2rem] text-center">{option.quantity}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  updateOptionQuantity(actualIndex, option.id, option.quantity + 1);
                }}
                className="h-8 w-8 p-0 rounded-full bg-orange-500 hover:bg-orange-600 text-white"
              >
                <Icon name="Plus" size={16} />
              </Button>
            </div>
          ) : (
            <span className="text-green-600 font-bold text-sm">
              {option.customPrice ? 'По запросу' : `+${option.price} ₽`}
            </span>
          )}
        </div>
        
        {option.enabled && option.voltageOptions && (
          <div className="mt-3 ml-8 flex gap-2">
            <Button
              size="sm"
              variant={option.selectedVoltage === '220V' ? 'default' : 'outline'}
              onClick={(e) => {
                e.stopPropagation();
                updateVoltage(actualIndex, option.id, '220V');
              }}
              className="h-7 text-xs"
            >
              220V ({option.voltageOptions['220V']} ₽)
            </Button>
            <Button
              size="sm"
              variant={option.selectedVoltage === '380V' ? 'default' : 'outline'}
              onClick={(e) => {
                e.stopPropagation();
                updateVoltage(actualIndex, option.id, '380V');
              }}
              className="h-7 text-xs"
            >
              380V ({option.voltageOptions['380V']} ₽)
            </Button>
          </div>
        )}
        
        {option.enabled && option.discount && (
          <div className={`text-xs mt-2 ml-8 ${hasDiscount ? 'text-green-700 font-semibold' : 'text-gray-500'}`}>
            {getDiscountLabel(option)}
            {hasDiscount && ' ✓ Применена!'}
          </div>
        )}
      </div>
    );
  };

  if (isSingleOption && singleOption) {
    const iconName = iconMap[container.productId] || 'Lightbulb';
    const colors = iconColorMap[container.productId] || { bg: 'from-amber-100 to-orange-100', icon: 'text-amber-600' };
    
    return (
      <Card 
        key={container.productId} 
        className="overflow-hidden bg-white border-2 border-gray-100 hover:border-blue-200 transition-all cursor-pointer shadow-sm"
        onClick={() => toggleContainer(actualIndex)}
      >
        <div className="p-3">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${colors.bg} flex items-center justify-center flex-shrink-0 transition-all ${container.expanded ? 'scale-110 shadow-lg' : ''}`}>
              <Icon name={iconName} size={24} className={`${colors.icon} transition-all`} />
            </div>
            
            <div className="flex-1">
              <h4 className="font-bold text-gray-800 text-sm uppercase tracking-wide truncate">
                {container.productName}
              </h4>
            </div>
            
            <div className="text-right">
              <div className="text-xs text-gray-500 mb-0.5">от</div>
              <div className="text-xl font-bold text-amber-600">
                {singleOption.price} <span className="text-base">₽</span>
              </div>
            </div>
            
            <Icon 
              name={container.expanded ? 'ChevronUp' : 'ChevronDown'} 
              size={20} 
              className="text-gray-400 flex-shrink-0"
            />
          </div>

          {container.expanded && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              {renderOption(singleOption)}
              
              {calculateContainerTotal(container) > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm text-gray-800">Итого за услугу:</span>
                    <span className="text-xl font-bold text-green-600">
                      {calculateContainerTotal(container).toLocaleString('ru-RU')} ₽
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    );
  }

  const constructionOptions = container.options.filter(opt => opt.group === 'construction' && !opt.isInfo);
  const panelOptions = container.options.filter(opt => opt.group === 'panel' && !opt.isInfo);
  const otherOptions = container.options.filter(opt => !opt.group && !opt.isInfo);
  const infoOptions = container.options.filter(opt => opt.isInfo);
  const iconName = iconMap[container.productId];
  const hasIcon = !!iconName;
  const colors = iconColorMap[container.productId] || { bg: 'from-slate-100 to-blue-100', icon: 'text-slate-700' };

  return (
    <Card 
      key={container.productId} 
      className="overflow-hidden bg-white border-2 border-gray-100 hover:border-blue-200 transition-all shadow-sm"
    >
      <div 
        className="p-3 flex items-center gap-3 cursor-pointer"
        onClick={() => toggleContainer(actualIndex)}
      >
        {hasIcon && (
          <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${colors.bg} flex items-center justify-center flex-shrink-0 transition-all ${container.expanded ? 'scale-110 shadow-lg' : ''}`}>
            <Icon name={iconName} size={24} className={`${colors.icon} transition-all`} />
          </div>
        )}
        
        <div className="flex-1">
          <h4 className="font-bold text-gray-800 text-sm uppercase tracking-wide truncate">
            {container.productName}
          </h4>
          {container.productDescription && (
            <p className="text-xs text-gray-500 mt-1">
              {container.productDescription}
            </p>
          )}
          {container.videoUrl && (
            <a
              href={container.videoUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white text-xs font-semibold rounded-full shadow-md hover:shadow-lg transition-all"
            >
              <Icon name="PlayCircle" size={14} />
              Видео-инструкция 60 сек
            </a>
          )}
        </div>
        
        <Icon 
          name={container.expanded ? 'ChevronUp' : 'ChevronDown'} 
          size={20} 
          className="text-gray-400 flex-shrink-0"
        />
      </div>

      {container.expanded && (
        <div className="px-3 pb-3 space-y-2">
          {otherOptions.length > 0 && (
            <div className="space-y-1.5">
              {otherOptions.map(renderOption)}
            </div>
          )}

          {constructionOptions.length > 0 && (
            <div>
              <button
                onClick={() => handleSectionToggle('construction')}
                className="w-full flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <span className="font-semibold text-sm text-blue-900">
                  Строительные работы
                </span>
                <Icon 
                  name={expandedSections.construction ? 'ChevronUp' : 'ChevronDown'} 
                  size={18} 
                  className="text-blue-600"
                />
              </button>
              {expandedSections.construction && (
                <div className="mt-1.5 space-y-1.5">
                  {constructionOptions.map(renderOption)}
                </div>
              )}
            </div>
          )}

          {panelOptions.length > 0 && (
            <div>
              <button
                onClick={() => handleSectionToggle('panel')}
                className="w-full flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <span className="font-semibold text-sm text-purple-900">
                  Работы в электрощите
                </span>
                <Icon 
                  name={expandedSections.panel ? 'ChevronUp' : 'ChevronDown'} 
                  size={18} 
                  className="text-purple-600"
                />
              </button>
              {expandedSections.panel && (
                <div className="mt-1.5 space-y-1.5">
                  {panelOptions.map(renderOption)}
                </div>
              )}
            </div>
          )}

          {infoOptions.length > 0 && (
            <div className="space-y-1.5 mt-2">
              {infoOptions.map(renderOption)}
            </div>
          )}

          {calculateContainerTotal(container) > 0 && (
            <div className="mt-3 pt-3 border-t-2 border-gray-200">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-sm text-gray-800">Итого за услугу:</span>
                <span className="text-xl font-bold text-green-600">
                  {calculateContainerTotal(container).toLocaleString('ru-RU')} ₽
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}