import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { googleAuth } from '@/lib/googleAuth';
import { googleCalendar } from '@/lib/googleCalendar';
import { googleKeep } from '@/lib/googleKeep';
import { Order } from '@/types/electrical';

interface GoogleIntegrationPanelProps {
  order: Order;
  onSync?: () => void;
}

export default function GoogleIntegrationPanel({ order, onSync }: GoogleIntegrationPanelProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [calendarSynced, setCalendarSynced] = useState(false);
  const [keepSynced, setKeepSynced] = useState(false);
  const [noteContent, setNoteContent] = useState('');

  useEffect(() => {
    setIsConnected(googleAuth.isAuthenticated());
    setCalendarSynced(!!order.googleCalendarEventId);
    setKeepSynced(!!order.googleKeepNoteId);
    
    const existingNote = googleKeep.getNote(order.id);
    if (existingNote) {
      setNoteContent(existingNote.content);
    }
  }, [order]);

  const handleConnect = () => {
    googleAuth.initiateOAuth();
  };

  const handleDisconnect = () => {
    if (confirm('Отключить интеграцию с Google? Существующие события и заметки сохранятся.')) {
      googleAuth.disconnect();
      setIsConnected(false);
    }
  };

  const handleSyncCalendar = async () => {
    setSyncing(true);
    try {
      if (calendarSynced && order.googleCalendarEventId) {
        await googleCalendar.updateEvent(order.googleCalendarEventId, order);
      } else {
        const event = await googleCalendar.createEvent(order);
        if (event) {
          setCalendarSynced(true);
          onSync?.();
        }
      }
    } catch (error) {
      console.error('Calendar sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncKeep = async () => {
    setSyncing(true);
    try {
      if (keepSynced) {
        await googleKeep.updateNote(order.id, noteContent);
      } else {
        const note = await googleKeep.createNote(order, noteContent);
        if (note) {
          setKeepSynced(true);
          onSync?.();
        }
      }
    } catch (error) {
      console.error('Keep sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  if (!isConnected) {
    return (
      <Card className="p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <Icon name="Calendar" size={24} className="text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">Интеграция с Google</h3>
            <p className="text-sm text-gray-600 mb-4">
              Подключите Google Calendar и Keep для автоматической синхронизации заявок, событий и заметок
            </p>
            <Button onClick={handleConnect} className="gap-2">
              <Icon name="Link" size={16} />
              Подключить Google
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          <Icon name="Calendar" size={20} className="text-blue-600" />
          Синхронизация с Google
        </h3>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDisconnect}
          className="gap-1"
        >
          <Icon name="Unlink" size={14} />
          Отключить
        </Button>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <Icon 
              name={calendarSynced ? "CheckCircle2" : "Calendar"} 
              size={20} 
              className={calendarSynced ? "text-green-600" : "text-gray-400"}
            />
            <div>
              <p className="font-medium">Google Calendar</p>
              <p className="text-xs text-gray-600">
                {calendarSynced ? 'Синхронизировано' : 'Не синхронизировано'}
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant={calendarSynced ? "outline" : "default"}
            onClick={handleSyncCalendar}
            disabled={syncing}
            className="gap-2"
          >
            <Icon name={calendarSynced ? "RefreshCw" : "Upload"} size={14} />
            {calendarSynced ? 'Обновить' : 'Синхронизировать'}
          </Button>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Icon 
                name={keepSynced ? "CheckCircle2" : "StickyNote"} 
                size={20} 
                className={keepSynced ? "text-green-600" : "text-gray-400"}
              />
              <div>
                <p className="font-medium">Google Keep</p>
                <p className="text-xs text-gray-600">
                  {keepSynced ? 'Заметка создана' : 'Создать заметку'}
                </p>
              </div>
            </div>
          </div>
          
          <textarea
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            placeholder="Добавьте заметки к заявке..."
            className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
          />
          
          <Button
            size="sm"
            variant={keepSynced ? "outline" : "default"}
            onClick={handleSyncKeep}
            disabled={syncing}
            className="gap-2 mt-2 w-full"
          >
            <Icon name={keepSynced ? "RefreshCw" : "Upload"} size={14} />
            {keepSynced ? 'Обновить заметку' : 'Создать заметку'}
          </Button>
        </div>

        {syncing && (
          <div className="flex items-center justify-center gap-2 text-sm text-gray-600 py-2">
            <Icon name="Loader2" size={16} className="animate-spin" />
            Синхронизация...
          </div>
        )}
      </div>
    </Card>
  );
}
