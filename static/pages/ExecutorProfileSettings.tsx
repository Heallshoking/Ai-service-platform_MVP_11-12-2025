import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import Icon from '@/components/ui/icon';
import PageHeader from '@/components/PageHeader';
import PageNavigation from '@/components/PageNavigation';
import ContactModal from '@/components/ContactModal';
import ExecutorStatsCard from '@/components/executor/ExecutorStatsCard';
import ProStatusModal from '@/components/executor/ProStatusModal';
import { useAuth } from '@/contexts/AuthContext';
import { RANKS, checkProStatus } from '@/types/electrical';

export default function ExecutorProfileSettings() {
  const navigate = useNavigate();
  const { user, updateUser, getExecutorProfile } = useAuth();
  const executorProfile = getExecutorProfile();

  const [hasCar, setHasCar] = useState(user?.hasCar || false);
  const [hasTools, setHasTools] = useState(user?.hasTools || false);
  const [isActive, setIsActive] = useState(user?.isActive || false);
  const [hasDiploma, setHasDiploma] = useState(user?.hasDiploma || false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showProModal, setShowProModal] = useState<'education' | 'car' | 'tools' | null>(null);
  
  const [diplomaFile, setDiplomaFile] = useState<File | null>(null);
  const [carFile, setCarFile] = useState<File | null>(null);
  const [toolsFile, setToolsFile] = useState<File | null>(null);
  
  const [hasChanges, setHasChanges] = useState(false);

  if (!executorProfile || !user) {
    navigate('/orders');
    return null;
  }

  const handleFileChange = (type: 'diploma' | 'car' | 'tools', file: File | null) => {
    if (type === 'diploma') {
      setDiplomaFile(file);
      setHasDiploma(true);
    }
    if (type === 'car') {
      setCarFile(file);
      setHasCar(true);
    }
    if (type === 'tools') {
      setToolsFile(file);
      setHasTools(true);
    }
    setHasChanges(true);
  };

  const handleChange = (field: string, value: any) => {
    setHasChanges(true);
    if (field === 'hasCar') setHasCar(value);
    if (field === 'hasTools') setHasTools(value);
    if (field === 'isActive') setIsActive(value);
    if (field === 'hasDiploma') setHasDiploma(value);
  };

  const handleSave = () => {
    const updates: any = {
      hasCar,
      hasTools,
      isActive,
      hasDiploma
    };

    if (diplomaFile) {
      updates.diplomaVerified = false;
    }
    if (carFile) {
      updates.carVerified = false;
    }
    if (toolsFile) {
      updates.toolsVerified = false;
    }

    const updatedProfile = { ...executorProfile, ...updates };
    const shouldBecomePro = checkProStatus(updatedProfile);

    if (shouldBecomePro) {
      updates.isPro = true;
      updates.proUnlockedAt = Date.now();
    }

    updateUser(updates);
    setHasChanges(false);
    navigate('/orders');
  };

  const currentRank = RANKS[executorProfile.rank];
  const isPro = executorProfile.isPro;

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 pb-24">
        <PageHeader />

        <div className="max-w-md mx-auto">
          <PageNavigation onContactClick={() => setShowContactModal(true)} />
          
          <div className="bg-white shadow-lg p-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-800">Профиль</h1>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <ExecutorStatsCard profile={executorProfile} />

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-gray-900">Статус "Профи"</h3>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="text-gray-400 hover:text-gray-600">
                        <Icon name="Info" className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p className="text-xs">Подтвердите диплом, автомобиль и инструменты для получения 50% от электромонтажных работ сразу</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
                {isPro ? (
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 px-3 py-1.5 rounded-full shadow-md">
                    <span className="text-xs font-bold text-white flex items-center gap-1">
                      <Icon name="Award" className="h-3 w-3" />
                      ПРОФИ
                    </span>
                  </div>
                ) : null}
              </div>

              <div className="space-y-3">
                {/* Образование */}
                <button
                  onClick={() => setShowProModal('education')}
                  className={`w-full border-2 rounded-lg p-4 transition-all text-left ${
                    user.diplomaVerified 
                      ? 'border-green-400 bg-green-50' 
                      : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                  }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${user.diplomaVerified ? 'bg-green-100' : 'bg-purple-100'}`}>
                        <Icon name="GraduationCap" className={`h-5 w-5 ${user.diplomaVerified ? 'text-green-600' : 'text-purple-600'}`} />
                      </div>
                      <div className="flex-1">
                        <Label className="text-sm font-semibold cursor-pointer">Добавить образование</Label>
                        <p className="text-xs text-gray-600 font-medium">💰 +10% к доходу за каждый заказ</p>
                      </div>
                    </div>
                    {user.diplomaVerified && (
                      <div className="flex items-center gap-1 px-2 py-1 bg-green-500 rounded-full">
                        <Icon name="CheckCircle" className="h-4 w-4 text-white" />
                        <span className="text-xs font-bold text-white">Подтверждено</span>
                      </div>
                    )}
                  </div>
                </button>

                {/* Автомобиль */}
                <button
                  onClick={() => setShowProModal('car')}
                  className={`w-full border-2 rounded-lg p-4 transition-all text-left ${
                    user.carVerified 
                      ? 'border-green-400 bg-green-50' 
                      : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                  }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${user.carVerified ? 'bg-green-100' : 'bg-blue-100'}`}>
                        <Icon name="Car" className={`h-5 w-5 ${user.carVerified ? 'text-green-600' : 'text-blue-600'}`} />
                      </div>
                      <div className="flex-1">
                        <Label className="text-sm font-semibold cursor-pointer">Автомобиль</Label>
                        <p className="text-xs text-gray-600 font-medium">🚗 +10% больше заказов от клиентов</p>
                      </div>
                    </div>
                    {user.carVerified && (
                      <div className="flex items-center gap-1 px-2 py-1 bg-green-500 rounded-full">
                        <Icon name="CheckCircle" className="h-4 w-4 text-white" />
                        <span className="text-xs font-bold text-white">Подтверждено</span>
                      </div>
                    )}
                  </div>
                </button>

                {/* Инструменты */}
                <button
                  onClick={() => setShowProModal('tools')}
                  className={`w-full border-2 rounded-lg p-4 transition-all text-left ${
                    user.toolsVerified 
                      ? 'border-green-400 bg-green-50' 
                      : 'border-gray-200 hover:border-orange-300 hover:bg-orange-50'
                  }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${user.toolsVerified ? 'bg-green-100' : 'bg-orange-100'}`}>
                        <Icon name="Wrench" className={`h-5 w-5 ${user.toolsVerified ? 'text-green-600' : 'text-orange-600'}`} />
                      </div>
                      <div className="flex-1">
                        <Label className="text-sm font-semibold cursor-pointer">Инструменты</Label>
                        <p className="text-xs text-gray-600 font-medium">🔧 +10% доверия и рейтинг</p>
                      </div>
                    </div>
                    {user.toolsVerified && (
                      <div className="flex items-center gap-1 px-2 py-1 bg-green-500 rounded-full">
                        <Icon name="CheckCircle" className="h-4 w-4 text-white" />
                        <span className="text-xs font-bold text-white">Подтверждено</span>
                      </div>
                    )}
                  </div>
                </button>

                {/* Активность */}
                <div className="border border-gray-200 rounded-lg p-3 hover:border-amber-200 transition-colors">
                  <div className="flex items-center gap-2">
                    <Switch checked={isActive} onCheckedChange={(val) => handleChange('isActive', val)} />
                    <div>
                      <Label className="text-sm font-medium">Принимаю заказы</Label>
                      <p className="text-xs text-gray-500 mt-0.5">+5% к доходу при активном статусе</p>
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button className="text-gray-400 hover:text-gray-600">
                          <Icon name="Info" className="h-3 w-3" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">+5% к доходу</p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                </div>
              </div>
            </Card>

            <div className="space-y-3">
              <Button 
                onClick={handleSave}
                disabled={!hasChanges}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed" 
                size="lg"
              >
                <Icon name="Save" className="mr-2 h-4 w-4" />
                Сохранить
              </Button>
              <Button 
                variant="outline" 
                onClick={() => navigate('/')} 
                className="w-full"
              >
                На главную
              </Button>
            </div>
          </div>
        </div>

        <ContactModal open={showContactModal} onClose={() => setShowContactModal(false)} />
        
        {showProModal && (
          <ProStatusModal
            type={showProModal}
            onClose={() => setShowProModal(null)}
            onSubmit={(file) => {
              if (showProModal === 'education') handleFileChange('diploma', file);
              if (showProModal === 'car') handleFileChange('car', file);
              if (showProModal === 'tools') handleFileChange('tools', file);
            }}
            isVerified={
              showProModal === 'education' ? user?.diplomaVerified :
              showProModal === 'car' ? user?.carVerified :
              user?.toolsVerified
            }
          />
        )}
      </div>
    </TooltipProvider>
  );
}