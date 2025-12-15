import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import PageHeader from '@/components/PageHeader';
import { useAuth } from '@/contexts/AuthContext';
import { RANKS, ExecutorProfile } from '@/types/electrical';

interface ExecutorWithDocs extends ExecutorProfile {
  name: string;
  phone: string;
  email?: string;
  diplomaUrl?: string;
  carDocsUrl?: string;
  toolsPhotoUrl?: string;
}

export default function AdminExecutors() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState('all');

  // Мок данные исполнителей с документами на проверке
  const [executors] = useState<ExecutorWithDocs[]>([
    {
      userId: '1',
      name: 'Петр Электрик',
      phone: '+7 900 000 0002',
      rank: 'specialist',
      completedOrders: 5,
      totalRevenue: 25000,
      registrationDate: Date.now() - 30 * 24 * 60 * 60 * 1000,
      hasDiploma: true,
      hasCar: true,
      hasTools: true,
      diplomaVerified: false,
      carVerified: false,
      toolsVerified: false,
      isActive: true,
      diplomaUrl: 'https://example.com/diploma.jpg',
      carDocsUrl: 'https://example.com/car.jpg',
      toolsPhotoUrl: 'https://example.com/tools.jpg'
    },
    {
      userId: '2',
      name: 'Алексей Мастеров',
      phone: '+7 900 000 0003',
      rank: 'master',
      completedOrders: 15,
      totalRevenue: 85000,
      registrationDate: Date.now() - 90 * 24 * 60 * 60 * 1000,
      hasDiploma: true,
      hasCar: true,
      hasTools: true,
      diplomaVerified: true,
      carVerified: true,
      toolsVerified: true,
      isPro: true,
      proUnlockedAt: Date.now() - 5 * 24 * 60 * 60 * 1000,
      isActive: true
    }
  ]);

  const filteredExecutors = useMemo(() => {
    return executors.filter(executor => {
      const matchesSearch = executor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           executor.phone.includes(searchQuery);
      
      if (filterTab === 'pending') {
        return matchesSearch && (
          (executor.hasDiploma && !executor.diplomaVerified) ||
          (executor.hasCar && !executor.carVerified) ||
          (executor.hasTools && !executor.toolsVerified)
        );
      }
      
      if (filterTab === 'pro') {
        return matchesSearch && executor.isPro;
      }
      
      return matchesSearch;
    });
  }, [executors, searchQuery, filterTab]);

  const handleVerifyDocument = (executorId: string, docType: 'diploma' | 'car' | 'tools', approved: boolean) => {
    console.log(`Verifying ${docType} for executor ${executorId}: ${approved ? 'approved' : 'rejected'}`);
    // Здесь будет логика обновления статуса документа
  };

  const pendingCount = executors.filter(e => 
    (e.hasDiploma && !e.diplomaVerified) ||
    (e.hasCar && !e.carVerified) ||
    (e.hasTools && !e.toolsVerified)
  ).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader title="Управление исполнителями" showBackButton />

      <div className="max-w-6xl mx-auto p-4 space-y-4">
        {/* Поиск */}
        <Card className="p-4">
          <div className="relative">
            <Icon name="Search" size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Поиск по имени или телефону..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </Card>

        {/* Фильтры */}
        <Tabs value={filterTab} onValueChange={setFilterTab}>
          <TabsList className="w-full grid grid-cols-3">
            <TabsTrigger value="all">
              Все ({executors.length})
            </TabsTrigger>
            <TabsTrigger value="pending" className="relative">
              На проверке ({pendingCount})
              {pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {pendingCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="pro">
              Профи
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {filteredExecutors.map(executor => (
              <ExecutorCard 
                key={executor.userId} 
                executor={executor}
                onVerify={handleVerifyDocument}
              />
            ))}
          </TabsContent>

          <TabsContent value="pending" className="space-y-4">
            {filteredExecutors.map(executor => (
              <ExecutorCard 
                key={executor.userId} 
                executor={executor}
                onVerify={handleVerifyDocument}
                showPendingOnly
              />
            ))}
          </TabsContent>

          <TabsContent value="pro" className="space-y-4">
            {filteredExecutors.map(executor => (
              <ExecutorCard 
                key={executor.userId} 
                executor={executor}
                onVerify={handleVerifyDocument}
              />
            ))}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

interface ExecutorCardProps {
  executor: ExecutorWithDocs;
  onVerify: (executorId: string, docType: 'diploma' | 'car' | 'tools', approved: boolean) => void;
  showPendingOnly?: boolean;
}

function ExecutorCard({ executor, onVerify, showPendingOnly }: ExecutorCardProps) {
  const currentRank = RANKS[executor.rank];
  const [expandedDocs, setExpandedDocs] = useState(false);

  const hasPendingDocs = 
    (executor.hasDiploma && !executor.diplomaVerified) ||
    (executor.hasCar && !executor.carVerified) ||
    (executor.hasTools && !executor.toolsVerified);

  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Заголовок */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{currentRank.badge}</div>
            <div>
              <h3 className="font-bold text-lg">{executor.name}</h3>
              <p className="text-sm text-gray-600">{executor.phone}</p>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  {currentRank.name}
                </Badge>
                {executor.isPro && (
                  <Badge className="bg-purple-500 text-xs">⭐ Профи</Badge>
                )}
              </div>
            </div>
          </div>

          {hasPendingDocs && (
            <Badge className="bg-orange-500">
              Ожидает проверки
            </Badge>
          )}
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-3 gap-3 py-3 border-y border-gray-200">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{executor.completedOrders}</p>
            <p className="text-xs text-gray-600">заказов</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {executor.totalRevenue.toLocaleString()}
            </p>
            <p className="text-xs text-gray-600">доход, ₽</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {Math.floor((Date.now() - executor.registrationDate) / (24 * 60 * 60 * 1000))}
            </p>
            <p className="text-xs text-gray-600">дней работы</p>
          </div>
        </div>

        {/* Документы */}
        {!showPendingOnly && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setExpandedDocs(!expandedDocs)}
            className="w-full"
          >
            <Icon name={expandedDocs ? 'ChevronUp' : 'ChevronDown'} className="h-4 w-4 mr-2" />
            {expandedDocs ? 'Скрыть документы' : 'Показать документы'}
          </Button>
        )}

        {(expandedDocs || showPendingOnly) && (
          <div className="space-y-3 pt-2">
            {/* Диплом */}
            {executor.hasDiploma && (
              <DocumentVerification
                title="Диплом специалиста"
                icon="GraduationCap"
                verified={executor.diplomaVerified}
                documentUrl={executor.diplomaUrl}
                onVerify={(approved) => onVerify(executor.userId, 'diploma', approved)}
              />
            )}

            {/* Автомобиль */}
            {executor.hasCar && (
              <DocumentVerification
                title="Документы на автомобиль"
                icon="Car"
                verified={executor.carVerified}
                documentUrl={executor.carDocsUrl}
                onVerify={(approved) => onVerify(executor.userId, 'car', approved)}
              />
            )}

            {/* Инструменты */}
            {executor.hasTools && (
              <DocumentVerification
                title="Фото инструментов"
                icon="Wrench"
                verified={executor.toolsVerified}
                documentUrl={executor.toolsPhotoUrl}
                onVerify={(approved) => onVerify(executor.userId, 'tools', approved)}
              />
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

interface DocumentVerificationProps {
  title: string;
  icon: string;
  verified?: boolean;
  documentUrl?: string;
  onVerify: (approved: boolean) => void;
}

function DocumentVerification({ title, icon, verified, documentUrl, onVerify }: DocumentVerificationProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon name={icon} className="h-4 w-4 text-gray-600" />
          <span className="text-sm font-medium">{title}</span>
        </div>
        {verified ? (
          <Badge className="bg-green-500 text-xs">
            <Icon name="CheckCircle" className="h-3 w-3 mr-1" />
            Проверено
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs">
            Ожидает
          </Badge>
        )}
      </div>

      {documentUrl && !verified && (
        <div className="space-y-2">
          <a 
            href={documentUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-blue-600 hover:underline"
          >
            <Icon name="ExternalLink" className="h-3 w-3" />
            Открыть документ
          </a>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onVerify(false)}
              className="flex-1 text-red-600 border-red-300 hover:bg-red-50"
            >
              <Icon name="X" className="h-4 w-4 mr-1" />
              Отклонить
            </Button>
            <Button
              size="sm"
              onClick={() => onVerify(true)}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <Icon name="Check" className="h-4 w-4 mr-1" />
              Подтвердить
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
