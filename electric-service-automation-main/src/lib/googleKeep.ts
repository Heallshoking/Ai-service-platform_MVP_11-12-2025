import { googleAuth } from './googleAuth';
import { Order, GoogleKeepNote } from '@/types/electrical';

export class GoogleKeepService {
  private static instance: GoogleKeepService;
  private notes: Map<string, GoogleKeepNote> = new Map();

  private constructor() {
    this.loadNotes();
  }

  static getInstance(): GoogleKeepService {
    if (!GoogleKeepService.instance) {
      GoogleKeepService.instance = new GoogleKeepService();
    }
    return GoogleKeepService.instance;
  }

  private loadNotes(): void {
    const stored = localStorage.getItem('google_keep_notes');
    if (stored) {
      const notesArray: GoogleKeepNote[] = JSON.parse(stored);
      this.notes = new Map(notesArray.map(note => [note.orderId, note]));
    }
  }

  private saveNotes(): void {
    const notesArray = Array.from(this.notes.values());
    localStorage.setItem('google_keep_notes', JSON.stringify(notesArray));
  }

  async createNote(order: Order, additionalContent?: string): Promise<GoogleKeepNote | null> {
    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      console.error('No valid access token');
      return null;
    }

    const settings = googleAuth.getSettings();
    if (!settings?.keepEnabled) {
      return null;
    }

    const title = `Заявка #${order.id.slice(-6)} - ${order.address}`;
    const content = this.formatNoteContent(order, additionalContent);

    const noteData = {
      title,
      textContent: content,
    };

    try {
      const response = await fetch('https://keep.googleapis.com/v1/notes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteData),
      });

      if (!response.ok) {
        console.warn('Google Keep API may not be available, storing locally');
        return this.createLocalNote(order, title, content);
      }

      const data = await response.json();

      const note: GoogleKeepNote = {
        id: crypto.randomUUID(),
        orderId: order.id,
        noteId: data.name,
        title,
        content,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      this.notes.set(order.id, note);
      this.saveNotes();

      return note;
    } catch (error) {
      console.warn('Google Keep API error, storing locally:', error);
      return this.createLocalNote(order, title, content);
    }
  }

  private createLocalNote(order: Order, title: string, content: string): GoogleKeepNote {
    const note: GoogleKeepNote = {
      id: crypto.randomUUID(),
      orderId: order.id,
      noteId: `local-${crypto.randomUUID()}`,
      title,
      content,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    this.notes.set(order.id, note);
    this.saveNotes();

    return note;
  }

  async updateNote(orderId: string, additionalContent: string): Promise<boolean> {
    const note = this.notes.get(orderId);
    if (!note) {
      return false;
    }

    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      return this.updateLocalNote(orderId, additionalContent);
    }

    const updatedContent = `${note.content}\n\n--- Обновление ---\n${additionalContent}`;

    if (note.noteId.startsWith('local-')) {
      return this.updateLocalNote(orderId, updatedContent);
    }

    try {
      const response = await fetch(`https://keep.googleapis.com/v1/${note.noteId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          textContent: updatedContent,
        }),
      });

      if (!response.ok) {
        return this.updateLocalNote(orderId, updatedContent);
      }

      note.content = updatedContent;
      note.updatedAt = Date.now();
      this.saveNotes();

      return true;
    } catch (error) {
      console.error('Error updating note:', error);
      return this.updateLocalNote(orderId, updatedContent);
    }
  }

  private updateLocalNote(orderId: string, content: string): boolean {
    const note = this.notes.get(orderId);
    if (!note) {
      return false;
    }

    note.content = content;
    note.updatedAt = Date.now();
    this.saveNotes();

    return true;
  }

  async deleteNote(orderId: string): Promise<boolean> {
    const note = this.notes.get(orderId);
    if (!note) {
      return false;
    }

    if (note.noteId.startsWith('local-')) {
      this.notes.delete(orderId);
      this.saveNotes();
      return true;
    }

    const token = await googleAuth.getValidAccessToken();
    if (!token) {
      this.notes.delete(orderId);
      this.saveNotes();
      return true;
    }

    try {
      const response = await fetch(`https://keep.googleapis.com/v1/${note.noteId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      this.notes.delete(orderId);
      this.saveNotes();

      return response.ok;
    } catch (error) {
      console.error('Error deleting note:', error);
      this.notes.delete(orderId);
      this.saveNotes();
      return true;
    }
  }

  getNote(orderId: string): GoogleKeepNote | undefined {
    return this.notes.get(orderId);
  }

  private formatNoteContent(order: Order, additionalContent?: string): string {
    const items = order.items.map(item => 
      `• ${item.product.name} x${item.quantity} - ${item.product.priceInstallOnly * item.quantity} ₽`
    ).join('\n');

    let content = `
📋 Заявка #${order.id.slice(-6)}
📅 Дата: ${new Date(order.date).toLocaleDateString('ru-RU')}
🕐 Время: ${order.time}
📍 Адрес: ${order.address}
📞 Телефон: ${order.phone}

💼 Услуги:
${items}

💰 Общая сумма: ${order.totalAmount?.toLocaleString() || 0} ₽
📊 Статус: ${this.getStatusLabel(order.status)}
${order.assignedToName ? `👤 Исполнитель: ${order.assignedToName}` : ''}
    `.trim();

    if (additionalContent) {
      content += `\n\n📝 Заметки:\n${additionalContent}`;
    }

    return content;
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

export const googleKeep = GoogleKeepService.getInstance();
