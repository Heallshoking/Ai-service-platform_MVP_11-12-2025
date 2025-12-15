import { Order } from '@/types/electrical';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const GOOGLE_CLIENT_SECRET = import.meta.env.VITE_GOOGLE_CLIENT_SECRET || '';

class GoogleTasksService {
  private accessToken: string | null = null;

  async createTask(order: Order, executorName: string): Promise<any> {
    if (!this.accessToken) {
      console.warn('Google Tasks: No access token');
      return null;
    }

    const taskData = {
      title: `Заявка #${order.id.slice(-6)}: ${order.customerName}`,
      notes: `
Адрес: ${order.address}
Телефон: ${order.customerPhone}
${order.customerEmail ? `Email: ${order.customerEmail}` : ''}
Дата: ${order.preferredDate ? new Date(order.preferredDate).toLocaleDateString('ru-RU') : 'Не указана'}

Услуги:
${order.items.map(item => `- ${item.name} x${item.quantity}`).join('\n')}

Стоимость: ${order.totalAmount.toLocaleString('ru-RU')} ₽
${order.notes ? `\nКомментарий: ${order.notes}` : ''}
      `.trim(),
      due: order.preferredDate ? new Date(order.preferredDate).toISOString() : undefined,
      status: 'needsAction'
    };

    try {
      const response = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        throw new Error(`Google Tasks API error: ${response.statusText}`);
      }

      const task = await response.json();
      return task;
    } catch (error) {
      console.error('Failed to create Google Task:', error);
      return null;
    }
  }

  async updateTask(taskId: string, order: Order): Promise<any> {
    if (!this.accessToken) {
      console.warn('Google Tasks: No access token');
      return null;
    }

    const taskData = {
      title: `Заявка #${order.id.slice(-6)}: ${order.customerName}`,
      notes: `
Адрес: ${order.address}
Телефон: ${order.customerPhone}
${order.customerEmail ? `Email: ${order.customerEmail}` : ''}
Дата: ${order.preferredDate ? new Date(order.preferredDate).toLocaleDateString('ru-RU') : 'Не указана'}

Услуги:
${order.items.map(item => `- ${item.name} x${item.quantity}`).join('\n')}

Стоимость: ${order.totalAmount.toLocaleString('ru-RU')} ₽
${order.notes ? `\nКомментарий: ${order.notes}` : ''}
      `.trim(),
      due: order.preferredDate ? new Date(order.preferredDate).toISOString() : undefined,
      status: order.status === 'completed' ? 'completed' : 'needsAction'
    };

    try {
      const response = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        throw new Error(`Google Tasks API error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update Google Task:', error);
      return null;
    }
  }

  async deleteTask(taskId: string): Promise<boolean> {
    if (!this.accessToken) {
      console.warn('Google Tasks: No access token');
      return false;
    }

    try {
      const response = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to delete Google Task:', error);
      return false;
    }
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  clearAccessToken() {
    this.accessToken = null;
  }
}

export const googleTasks = new GoogleTasksService();
