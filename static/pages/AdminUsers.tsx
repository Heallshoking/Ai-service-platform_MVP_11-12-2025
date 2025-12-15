import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { toast } from '@/hooks/use-toast';

interface User {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: 'client' | 'executor' | 'admin';
  status: 'active' | 'blocked';
  ordersCount: number;
  rating?: number;
  joinDate: string;
}

const mockUsers: User[] = [
  {
    id: 1,
    name: 'Алексей Иванов',
    email: 'alexey@example.com',
    phone: '+7 (912) 345-67-89',
    role: 'executor',
    status: 'active',
    ordersCount: 156,
    rating: 4.9,
    joinDate: '15.01.2023'
  },
  {
    id: 2,
    name: 'Мария Петрова',
    email: 'maria@example.com',
    phone: '+7 (923) 456-78-90',
    role: 'client',
    status: 'active',
    ordersCount: 12,
    joinDate: '20.06.2023'
  },
  {
    id: 3,
    name: 'Дмитрий Смирнов',
    email: 'dmitry@example.com',
    phone: '+7 (934) 567-89-01',
    role: 'executor',
    status: 'active',
    ordersCount: 98,
    rating: 4.8,
    joinDate: '10.03.2023'
  },
  {
    id: 4,
    name: 'Анна Козлова',
    email: 'anna@example.com',
    phone: '+7 (945) 678-90-12',
    role: 'client',
    status: 'blocked',
    ordersCount: 3,
    joinDate: '05.09.2024'
  }
];

const AdminUsers = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'client' | 'executor' | 'admin'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'blocked'>('all');

  const handleToggleStatus = (userId: number) => {
    setUsers(users.map(user => 
      user.id === userId 
        ? { ...user, status: user.status === 'active' ? 'blocked' : 'active' as 'active' | 'blocked' }
        : user
    ));
    toast({
      title: "Статус изменен",
      description: "Статус пользователя обновлен"
    });
  };

  const handleChangeRole = (userId: number, newRole: 'client' | 'executor' | 'admin') => {
    setUsers(users.map(user => 
      user.id === userId ? { ...user, role: newRole } : user
    ));
    toast({
      title: "Роль изменена",
      description: "Роль пользователя обновлена"
    });
  };

  const getRoleName = (role: string) => {
    const roles = {
      client: 'Клиент',
      executor: 'Исполнитель',
      admin: 'Администратор'
    };
    return roles[role as keyof typeof roles] || role;
  };

  const getRoleColor = (role: string) => {
    const colors = {
      client: 'secondary',
      executor: 'default',
      admin: 'destructive'
    };
    return colors[role as keyof typeof colors] as any || 'secondary';
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.phone.includes(searchQuery);
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-background pb-8">
      <header className="border-b border-border bg-card sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => navigate('/admin-panel')} className="gap-2">
              <Icon name="ArrowLeft" size={20} />
              Назад
            </Button>
            <h1 className="font-heading font-bold text-lg">Управление пользователями</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <Card className="p-6">
            <div className="flex flex-col gap-4 mb-6">
              <Input
                placeholder="Поиск по имени, email или телефону..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-12"
              />
              <div className="flex gap-4">
                <Select value={roleFilter} onValueChange={(v: any) => setRoleFilter(v)}>
                  <SelectTrigger className="flex-1 h-12">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все роли</SelectItem>
                    <SelectItem value="client">Клиенты</SelectItem>
                    <SelectItem value="executor">Исполнители</SelectItem>
                    <SelectItem value="admin">Администраторы</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={(v: any) => setStatusFilter(v)}>
                  <SelectTrigger className="flex-1 h-12">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все статусы</SelectItem>
                    <SelectItem value="active">Активные</SelectItem>
                    <SelectItem value="blocked">Заблокированные</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-3">
              {filteredUsers.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Icon name="Users" size={64} className="mx-auto mb-4 opacity-30" />
                  <p>Пользователи не найдены</p>
                </div>
              ) : (
                filteredUsers.map((user) => (
                  <Card key={user.id} className="p-4">
                    <div className="flex items-start gap-4">
                      <Avatar className="h-16 w-16">
                        <AvatarFallback className="bg-primary/10 text-primary text-xl">
                          {user.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div>
                            <h3 className="font-bold text-lg">{user.name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant={getRoleColor(user.role)}>
                                {getRoleName(user.role)}
                              </Badge>
                              <Badge variant={user.status === 'active' ? 'default' : 'destructive'}>
                                {user.status === 'active' ? 'Активен' : 'Заблокирован'}
                              </Badge>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-muted-foreground">
                              Заказов: {user.ordersCount}
                            </div>
                            {user.rating && (
                              <div className="flex items-center gap-1 justify-end mt-1">
                                <Icon name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                                <span className="font-semibold">{user.rating}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Icon name="Mail" size={14} />
                            <span>{user.email}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Icon name="Phone" size={14} />
                            <span>{user.phone}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Icon name="Calendar" size={14} />
                            <span>Регистрация: {user.joinDate}</span>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Select 
                            value={user.role} 
                            onValueChange={(v: any) => handleChangeRole(user.id, v)}
                          >
                            <SelectTrigger className="w-48 h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="client">Клиент</SelectItem>
                              <SelectItem value="executor">Исполнитель</SelectItem>
                              <SelectItem value="admin">Администратор</SelectItem>
                            </SelectContent>
                          </Select>

                          <Button 
                            size="sm" 
                            variant={user.status === 'active' ? 'destructive' : 'default'}
                            onClick={() => handleToggleStatus(user.id)}
                          >
                            <Icon name={user.status === 'active' ? 'Ban' : 'CheckCircle2'} size={16} className="mr-2" />
                            {user.status === 'active' ? 'Заблокировать' : 'Разблокировать'}
                          </Button>

                          <Button size="sm" variant="outline">
                            <Icon name="Eye" size={16} className="mr-2" />
                            Подробнее
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default AdminUsers;
