import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Label } from './ui/label';

interface Executor {
  id: number;
  name: string;
  rating: number;
  experience_years: number;
}

interface ExecutorSelectProps {
  executors: Executor[];
  value: number | null;
  onChange: (value: number | null) => void;
}

const ExecutorSelect = ({ executors, value, onChange }: ExecutorSelectProps) => {
  return (
    <div className="space-y-2">
      <Label>Выберите мастера (необязательно)</Label>
      <Select
        value={value?.toString() || '0'}
        onValueChange={(val) => onChange(val === '0' ? null : parseInt(val))}
      >
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="0">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">⚡</span>
              <span>Любой свободный исполнитель</span>
            </div>
          </SelectItem>
          {executors.map((executor) => (
            <SelectItem key={executor.id} value={executor.id.toString()}>
              <div className="flex items-center gap-2">
                <span>👷</span>
                <div>
                  <p className="font-medium">{executor.name}</p>
                  <p className="text-xs text-muted-foreground">
                    ⭐ {executor.rating} • Стаж: {executor.experience_years} лет
                  </p>
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default ExecutorSelect;
