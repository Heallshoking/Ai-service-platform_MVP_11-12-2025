import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import TasksButton from '@/components/TasksButton';

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  getTotalItems: () => number;
}

export default function BottomNav({ activeTab, setActiveTab, getTotalItems }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border shadow-lg z-40">
      <div className="container mx-auto px-2 py-3">
        <div className="flex justify-around items-center max-w-md mx-auto">
          <Button
            variant={activeTab === 'home' ? 'default' : 'ghost'}
            size="sm"
            className="flex-col h-auto py-2 gap-1"
            onClick={() => setActiveTab('home')}
          >
            <Icon name="Home" size={20} />
            <span className="text-[10px] font-medium">Главная</span>
          </Button>

          <Button
            variant={activeTab === 'calculator' ? 'default' : 'ghost'}
            size="sm"
            className="flex-col h-auto py-2 gap-1"
            onClick={() => setActiveTab('calculator')}
          >
            <Icon name="Calculator" size={20} />
            <span className="text-[10px] font-medium">Калькулятор</span>
          </Button>

          <Button
            variant={activeTab === 'order' ? 'default' : 'ghost'}
            size="sm"
            className="flex-col h-auto py-2 gap-1 relative"
            onClick={() => setActiveTab('order')}
          >
            <Icon name="ShoppingCart" size={20} />
            <span className="text-[10px] font-medium">Заявка</span>
            {getTotalItems() > 0 && (
              <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
                {getTotalItems()}
              </span>
            )}
          </Button>

          <TasksButton />
        </div>
      </div>
    </nav>
  );
}
