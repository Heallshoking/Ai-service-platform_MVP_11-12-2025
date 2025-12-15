import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';

export default function FeedbackButton() {
  const [open, setOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (feedback.trim()) {
      try {
        const response = await fetch('https://functions.poehali.dev/5c5ceed0-7356-491d-8f3c-01e20dede751', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ feedback: feedback.trim() }),
        });

        if (response.ok) {
          setSubmitted(true);
          setTimeout(() => {
            setOpen(false);
            setFeedback('');
            setSubmitted(false);
          }, 2000);
        } else {
          console.error('Ошибка отправки фидбека');
        }
      } catch (error) {
        console.error('Ошибка отправки фидбека:', error);
      }
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-br from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-white rounded-full p-4 shadow-xl hover:shadow-2xl transition-all hover:scale-110 z-50 group"
        title="Предложить идею"
      >
        <Icon name="Lightbulb" size={26} className="drop-shadow-md" />
        <span className="absolute -top-1 -right-1 text-2xl animate-pulse">
          💡
        </span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Icon name="Sparkles" size={20} className="text-yellow-500" />
              У вас есть идея?
            </DialogTitle>
            <DialogDescription className="text-left sm:text-center">
              Предлагайте свои идеи по улучшению сервиса для электриков и их клиентов
            </DialogDescription>
          </DialogHeader>

          {!submitted ? (
            <div className="space-y-4">
              <Textarea
                placeholder="Расскажите, что можно улучшить или какую функцию добавить..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={5}
                className="resize-none"
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleSubmit}
                  disabled={!feedback.trim()}
                  className="flex-1"
                >
                  <Icon name="Send" size={16} className="mr-2" />
                  Отправить
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setOpen(false)}
                >
                  Отмена
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <Icon name="Check" size={32} className="text-green-600" />
              </div>
              <p className="text-lg font-semibold text-gray-800">Спасибо за фидбек!</p>
              <p className="text-sm text-gray-600 mt-2">Мы обязательно рассмотрим ваше предложение</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}