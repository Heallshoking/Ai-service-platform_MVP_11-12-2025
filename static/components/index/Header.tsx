import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/hooks/use-toast';

export default function Header() {
  const { user, isAuthenticated } = useAuth();

  return (
    <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
      <div className="w-full px-4 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <Icon name="Zap" className="text-primary" size={24} />
            <div>
              <h1 className="font-heading font-bold text-lg text-foreground">БАЛТСЕТЬ <sup className="text-xs text-primary">³⁹</sup></h1>
              <p className="text-[10px] text-muted-foreground uppercase">Калининград</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-muted-foreground hover:text-primary text-xs"
              onClick={() => toast({ title: "Идея принята", description: "Спасибо за ваше участие в развитии сервиса!" })}
            >
              <Icon name="Lightbulb" size={16} />
              <span className="hidden sm:inline">Идея</span>
            </Button>
            {isAuthenticated ? (
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-2"
                onClick={() => window.location.href = user?.role === 'admin' ? '/admin' : user?.role === 'executor' ? '/executor' : '/profile'}
              >
                <Icon name="User" size={18} />
                <span className="hidden md:inline text-sm">{user?.name}</span>
              </Button>
            ) : null}
            <a href="tel:+74012520725" className="text-sm md:text-base font-bold text-primary hover:text-primary/80 transition-colors">
              +7 (4012) 52-07-25
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}