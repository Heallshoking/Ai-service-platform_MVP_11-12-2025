import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { Service, quickServices, electricalServices } from '@/types/services';
import { toast } from '@/hooks/use-toast';

const AdminProducts = () => {
  const navigate = useNavigate();
  const [services, setServices] = useState<Service[]>([...quickServices, ...electricalServices]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<'all' | 'quick' | 'electrical'>('all');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    oldPrice: '',
    discount: '',
    category: 'electrical' as 'quick' | 'electrical',
    icon: 'Wrench'
  });

  const handleOpenDialog = (service?: Service) => {
    if (service) {
      setEditingService(service);
      setFormData({
        name: service.name,
        description: service.description,
        price: service.price.toString(),
        oldPrice: service.oldPrice?.toString() || '',
        discount: service.discount?.toString() || '',
        category: service.category,
        icon: service.icon || 'Wrench'
      });
    } else {
      setEditingService(null);
      setFormData({
        name: '',
        description: '',
        price: '',
        oldPrice: '',
        discount: '',
        category: 'electrical',
        icon: 'Wrench'
      });
    }
    setIsDialogOpen(true);
  };

  const handleSave = () => {
    if (!formData.name || !formData.description || !formData.price) {
      toast({
        title: "Ошибка",
        description: "Заполните все обязательные поля",
        variant: "destructive"
      });
      return;
    }

    const serviceData: Service = {
      id: editingService?.id || `new-${Date.now()}`,
      name: formData.name,
      description: formData.description,
      price: parseFloat(formData.price),
      oldPrice: formData.oldPrice ? parseFloat(formData.oldPrice) : undefined,
      discount: formData.discount ? parseFloat(formData.discount) : undefined,
      category: formData.category,
      icon: formData.icon
    };

    if (editingService) {
      setServices(services.map(s => s.id === editingService.id ? serviceData : s));
      toast({
        title: "Сохранено",
        description: "Услуга обновлена"
      });
    } else {
      setServices([...services, serviceData]);
      toast({
        title: "Добавлено",
        description: "Новая услуга создана"
      });
    }

    setIsDialogOpen(false);
  };

  const handleDelete = (serviceId: string) => {
    if (confirm('Удалить эту услугу?')) {
      setServices(services.filter(s => s.id !== serviceId));
      toast({
        title: "Удалено",
        description: "Услуга удалена из каталога"
      });
    }
  };

  const filteredServices = services.filter(service => {
    const matchesSearch = service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         service.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || service.category === categoryFilter;
    return matchesSearch && matchesCategory;
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
            <h1 className="font-heading font-bold text-lg">Управление товарами</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1">
                <Input
                  placeholder="Поиск по названию или описанию..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-12"
                />
              </div>
              <Select value={categoryFilter} onValueChange={(v: any) => setCategoryFilter(v)}>
                <SelectTrigger className="w-full sm:w-64 h-12">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все категории</SelectItem>
                  <SelectItem value="quick">Вызов электрика</SelectItem>
                  <SelectItem value="electrical">Электромонтаж</SelectItem>
                </SelectContent>
              </Select>
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="lg" onClick={() => handleOpenDialog()} className="gap-2">
                    <Icon name="Plus" size={20} />
                    Добавить услугу
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>
                      {editingService ? 'Редактировать услугу' : 'Новая услуга'}
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <Label>Название услуги *</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Например: Установка розетки"
                      />
                    </div>
                    <div>
                      <Label>Описание *</Label>
                      <Textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Краткое описание услуги"
                        rows={3}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Цена * (₽)</Label>
                        <Input
                          type="number"
                          value={formData.price}
                          onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                          placeholder="1000"
                        />
                      </div>
                      <div>
                        <Label>Старая цена (₽)</Label>
                        <Input
                          type="number"
                          value={formData.oldPrice}
                          onChange={(e) => setFormData({ ...formData, oldPrice: e.target.value })}
                          placeholder="1500"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Скидка (%)</Label>
                        <Input
                          type="number"
                          value={formData.discount}
                          onChange={(e) => setFormData({ ...formData, discount: e.target.value })}
                          placeholder="20"
                        />
                      </div>
                      <div>
                        <Label>Категория *</Label>
                        <Select value={formData.category} onValueChange={(v: any) => setFormData({ ...formData, category: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="quick">Вызов электрика</SelectItem>
                            <SelectItem value="electrical">Электромонтаж</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" className="flex-1" onClick={() => setIsDialogOpen(false)}>
                        Отмена
                      </Button>
                      <Button className="flex-1" onClick={handleSave}>
                        Сохранить
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <div className="space-y-3">
              {filteredServices.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Icon name="Package" size={64} className="mx-auto mb-4 opacity-30" />
                  <p>Услуги не найдены</p>
                </div>
              ) : (
                filteredServices.map((service) => (
                  <Card key={service.id} className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Icon name={service.icon as any} size={24} className="text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div>
                            <h3 className="font-bold text-lg">{service.name}</h3>
                            <Badge variant="secondary" className="mt-1">
                              {service.category === 'quick' ? 'Вызов электрика' : 'Электромонтаж'}
                            </Badge>
                          </div>
                          <div className="text-right">
                            {service.oldPrice && (
                              <div className="text-sm text-muted-foreground line-through">
                                {service.oldPrice.toLocaleString()} ₽
                              </div>
                            )}
                            <div className="font-bold text-xl text-primary">
                              {service.price.toLocaleString()} ₽
                            </div>
                            {service.discount && (
                              <Badge variant="destructive" className="mt-1">
                                -{service.discount}%
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{service.description}</p>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => handleOpenDialog(service)}>
                            <Icon name="Edit" size={16} className="mr-2" />
                            Редактировать
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDelete(service.id)}>
                            <Icon name="Trash2" size={16} className="mr-2" />
                            Удалить
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

export default AdminProducts;
