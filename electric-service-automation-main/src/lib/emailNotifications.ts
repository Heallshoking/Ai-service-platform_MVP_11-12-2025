import { Order } from '@/types/electrical';

const EMAIL_API_URL = 'https://functions.poehali.dev/844c657d-c59c-4e46-a6dc-f58689204e01';
const ADMIN_EMAIL = 'electro.me@yandex.ru';

export async function sendOrderNotification(order: Order): Promise<void> {
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }
        .order-id { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .info-row { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }
        .label { font-weight: bold; color: #667eea; }
        .items { margin-top: 20px; }
        .item { background: white; padding: 10px; margin: 5px 0; border-left: 3px solid #667eea; }
        .footer { margin-top: 20px; padding: 15px; background: #667eea; color: white; text-align: center; border-radius: 4px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🔌 Новая заявка на электромонтаж</h1>
          <div class="order-id">Заявка #${order.id.slice(-6)}</div>
        </div>
        
        <div class="content">
          <div class="info-row">
            <span class="label">📞 Телефон:</span> ${order.phone}
          </div>
          
          <div class="info-row">
            <span class="label">📍 Адрес:</span> ${order.address}
          </div>
          
          <div class="info-row">
            <span class="label">📅 Дата и время:</span> ${order.date} в ${order.time}
          </div>
          
          <div class="info-row">
            <span class="label">💰 Сумма:</span> ${order.totalAmount?.toLocaleString('ru-RU')} ₽
          </div>
          
          <div class="items">
            <h3>Состав заказа:</h3>
            ${order.items.map(item => `
              <div class="item">
                <strong>${item.name}</strong><br>
                Количество: ${item.quantity} шт. × ${item.price.toLocaleString('ru-RU')} ₽ = ${(item.quantity * item.price).toLocaleString('ru-RU')} ₽
                ${item.description ? `<br><small>${item.description}</small>` : ''}
              </div>
            `).join('')}
          </div>
          
          ${order.totalSwitches ? `
            <div class="info-row">
              <span class="label">📊 Итого:</span><br>
              Выключателей: ${order.totalSwitches} шт.<br>
              Розеток: ${order.totalOutlets} шт.<br>
              Точек: ${order.totalPoints} шт.<br>
              Кабеля (оценка): ${order.estimatedCable} м<br>
              Рамок: ${order.estimatedFrames} шт.
            </div>
          ` : ''}
        </div>
        
        <div class="footer">
          <p>Создано: ${new Date(order.createdAt).toLocaleString('ru-RU')}</p>
          <p>Статус: <strong>${getStatusText(order.status)}</strong></p>
        </div>
      </div>
    </body>
    </html>
  `;

  try {
    const response = await fetch(EMAIL_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        to: ADMIN_EMAIL,
        subject: `🔌 Новая заявка #${order.id.slice(-6)} на ${order.totalAmount?.toLocaleString('ru-RU')} ₽`,
        html
      })
    });

    if (!response.ok) {
      throw new Error(`Email API error: ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to send email notification:', error);
  }
}

export async function sendStatusUpdateNotification(order: Order, oldStatus: string): Promise<void> {
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }
        .status-change { background: white; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .old-status { color: #9ca3af; text-decoration: line-through; }
        .new-status { color: #10b981; font-weight: bold; font-size: 18px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📋 Обновление статуса заявки</h1>
          <div style="font-size: 20px; margin-top: 10px;">Заявка #${order.id.slice(-6)}</div>
        </div>
        
        <div class="content">
          <div class="status-change">
            <p>Статус изменён:</p>
            <div class="old-status">${getStatusText(oldStatus)}</div>
            <div style="font-size: 30px; margin: 10px 0;">↓</div>
            <div class="new-status">${getStatusText(order.status)}</div>
          </div>
          
          <div style="background: white; padding: 15px; border-radius: 4px; margin-top: 15px;">
            <p><strong>📞 Телефон:</strong> ${order.phone}</p>
            <p><strong>📍 Адрес:</strong> ${order.address}</p>
            <p><strong>💰 Сумма:</strong> ${order.totalAmount?.toLocaleString('ru-RU')} ₽</p>
            ${order.electricianName ? `<p><strong>👷 Исполнитель:</strong> ${order.electricianName}</p>` : ''}
          </div>
        </div>
      </div>
    </body>
    </html>
  `;

  try {
    const response = await fetch(EMAIL_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        to: ADMIN_EMAIL,
        subject: `📋 Заявка #${order.id.slice(-6)}: ${getStatusText(order.status)}`,
        html
      })
    });

    if (!response.ok) {
      throw new Error(`Email API error: ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to send status update notification:', error);
  }
}

function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': '⏳ Ожидает подтверждения',
    'confirmed': '✅ Подтверждена',
    'in-progress': '🔧 В работе',
    'completed': '✔️ Завершена'
  };
  return statusMap[status] || status;
}
