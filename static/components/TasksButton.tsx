import { Button } from './ui/button';
import Icon from './ui/icon';

interface TasksButtonProps {
  count: number;
  onClick: () => void;
}

const TasksButton = ({ count, onClick }: TasksButtonProps) => {
  return (
    <Button
      size="lg"
      className="relative w-full md:w-auto"
      onClick={onClick}
    >
      <Icon name="ListTodo" size={20} className="mr-2" />
      <span>Задачи</span>
      {count > 0 && (
        <span className="ml-2 bg-white text-primary font-bold px-2.5 py-0.5 rounded-full text-sm">
          {count}
        </span>
      )}
    </Button>
  );
};

export default TasksButton;
