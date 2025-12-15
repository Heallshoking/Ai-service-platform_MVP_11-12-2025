import { useState } from 'react';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface Category {
  id: string;
  name: string;
  icon: string;
  services: string[];
}

const CATEGORIES: Category[] = [
  {
    id: 'electric',
    name: 'Электрика',
    icon: 'Zap',
    services: ['Розетки', 'Выключатели', 'Проводка', 'Щиты']
  },
  {
    id: 'lighting',
    name: 'Освещение',
    icon: 'Lightbulb',
    services: ['Люстры', 'Светильники', 'Подсветка']
  }
];

export default function CategorySection() {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  return (
    <div className="space-y-2 mb-2">
      <h3 className="text-sm font-semibold text-gray-700 px-1">Быстрый расчёт</h3>
      <div className="grid gap-2">
        {CATEGORIES.map((category) => {
          const isExpanded = expandedCategory === category.id;
          
          return (
            <Card 
              key={category.id} 
              className="overflow-hidden transition-all cursor-pointer hover:shadow-md"
              onClick={() => setExpandedCategory(isExpanded ? null : category.id)}
            >
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                      <Icon name={category.icon as any} className="text-primary" size={18} />
                    </div>
                    <span className="font-semibold text-sm">{category.name}</span>
                  </div>
                  <Icon 
                    name={isExpanded ? 'ChevronUp' : 'ChevronDown'} 
                    className="text-muted-foreground" 
                    size={18} 
                  />
                </div>
                
                {isExpanded && (
                  <div className="mt-2.5 pt-2.5 border-t border-gray-100">
                    <div className="flex flex-wrap gap-1.5">
                      {category.services.map((service, idx) => (
                        <span 
                          key={idx}
                          className="inline-block px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium"
                        >
                          {service}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
