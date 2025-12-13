import { googleAuth } from './googleAuth';
import { Order, GoogleCalendarEvent } from '@/types/electrical';

export class GoogleCalendarService {
  private static instance: GoogleCalendarService;

  private constructor() {}

  static getInstance(): GoogleCalendarService {
    if (!GoogleCalendarService.instance) {
      GoogleCalendarService.instance = new GoogleCalendarService();
    }
    return GoogleCalendarService.instance;
  }

  async createEvent(order: Order): Promise<GoogleCalendarEvent | null> {
    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      console.error('No valid access token');
      return null;
    }

    const settings = googleAuth.getSettings();
    if (!settings?.calendarEnabled) {
      return null;
    }

    const [hours, minutes] = order.time.split(':');
    const startDate = new Date(order.date);
    startDate.setHours(parseInt(hours), parseInt(minutes), 0);
    
    const endDate = new Date(startDate);
    endDate.setHours(startDate.getHours() + 2);

    const event = {
      summary: `Электромонтажные работы #${order.id.slice(-6)}`,
      description: this.formatOrderDescription(order),
      location: order.address,
      start: {
        dateTime: startDate.toISOString(),
        timeZone: 'Europe/Moscow',
      },
      end: {
        dateTime: endDate.toISOString(),
        timeZone: 'Europe/Moscow',
      },
      reminders: {
        useDefault: false,
        overrides: [
          { method: 'popup', minutes: 60 },
          { method: 'popup', minutes: 30 },
        ],
      },
    };

    try {
      const response = await fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      });

      if (!response.ok) {
        throw new Error('Failed to create calendar event');
      }

      const data = await response.json();

      const calendarEvent: GoogleCalendarEvent = {
        id: crypto.randomUUID(),
        orderId: order.id,
        eventId: data.id,
        summary: event.summary,
        description: event.description,
        startTime: startDate.toISOString(),
        endTime: endDate.toISOString(),
        location: order.address,
        status: 'confirmed',
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      return calendarEvent;
    } catch (error) {
      console.error('Error creating calendar event:', error);
      return null;
    }
  }

  async updateEvent(eventId: string, order: Order): Promise<boolean> {
    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      return false;
    }

    const [hours, minutes] = order.time.split(':');
    const startDate = new Date(order.date);
    startDate.setHours(parseInt(hours), parseInt(minutes), 0);
    
    const endDate = new Date(startDate);
    endDate.setHours(startDate.getHours() + 2);

    const event = {
      summary: `Электромонтажные работы #${order.id.slice(-6)}`,
      description: this.formatOrderDescription(order),
      location: order.address,
      start: {
        dateTime: startDate.toISOString(),
        timeZone: 'Europe/Moscow',
      },
      end: {
        dateTime: endDate.toISOString(),
        timeZone: 'Europe/Moscow',
      },
    };

    try {
      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(event),
        }
      );

      return response.ok;
    } catch (error) {
      console.error('Error updating calendar event:', error);
      return false;
    }
  }

  async deleteEvent(eventId: string): Promise<boolean> {
    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      return false;
    }

    try {
      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      return response.ok;
    } catch (error) {
      console.error('Error deleting calendar event:', error);
      return false;
    }
  }

  private formatOrderDescription(order: Order): string {
    const items = order.items.map(item => 
      `• ${item.product.name} x${item.quantity}`
    ).join('\n');

    return `
Заявка: #${order.id.slice(-6)}
Статус: ${this.getStatusLabel(order.status)}
Телефон: ${order.phone}

Услуги:
${items}

Общая сумма: ${order.totalAmount?.toLocaleString() || 0} ₽
${order.assignedToName ? `\nИсполнитель: ${order.assignedToName}` : ''}
    `.trim();
  }

  private getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      'pending': 'Ожидает',
      'confirmed': 'Подтверждена',
      'in-progress': 'В работе',
      'completed': 'Завершена',
    };
    return labels[status] || status;
  }
}

export const googleCalendar = GoogleCalendarService.getInstance();
