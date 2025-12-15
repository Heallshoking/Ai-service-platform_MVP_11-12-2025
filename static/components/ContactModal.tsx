import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

interface ContactModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ContactModal({ open, onClose }: ContactModalProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center">Связаться с нами</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <a
            href="tel:+74012520725"
            className="flex items-center gap-4 p-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Icon name="Phone" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold">Позвонить</p>
              <p className="text-sm opacity-90">+7 (4012) 52-07-25</p>
            </div>
          </a>

          <a
            href="https://vk.com/im?sel=-23524557"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Icon name="MessageCircle" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold">ВКонтакте</p>
              <p className="text-sm opacity-90">Написать сообщение</p>
            </div>
          </a>

          <a
            href="https://wa.me/74012520725"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Icon name="MessageSquare" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold">WhatsApp</p>
              <p className="text-sm opacity-90">Быстрая связь</p>
            </div>
          </a>

          <div className="bg-gray-50 rounded-xl p-4 border-2 border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <Icon name="MapPin" size={24} className="text-blue-600" />
              <h3 className="font-semibold text-gray-800">Мы в Калининграде</h3>
            </div>
            <p className="text-sm text-gray-600">
              Работаем по всему городу и области
            </p>
            <p className="text-sm text-gray-600 mt-2">
              🕐 Пн-Сб: 10:00 - 18:00
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Воскресенье — выходной
            </p>
          </div>

          <a
            href="https://yandex.ru/maps/org/159261695633"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Icon name="Star" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold">Отзывы</p>
              <p className="text-sm opacity-90">Оцените нашу работу</p>
            </div>
          </a>

          <a
            href="https://vk.com/konig_electric"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Icon name="Image" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold">Портфолио</p>
              <p className="text-sm opacity-90">Наши работы</p>
            </div>
          </a>

          <Button
            onClick={onClose}
            variant="outline"
            className="w-full h-12"
          >
            Закрыть
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}