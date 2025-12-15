// Universal Chat Widget for all pages

class ChatWidget {
  constructor() {
    this.isOpen = false;
    this.messages = [];
    this.step = 'GREETING';
    this.data = {};
    this.init();
  }

  init() {
    this.injectHTML();
    this.attachEvents();
    this.addBotMessage('👋 Здравствуйте! Я помогу рассчитать стоимость электромонтажных работ.\n\n💡 Что вас интересует?', 'greeting-buttons');
  }

  injectHTML() {
    const html = `
      <!-- Floating Chat Button -->
      <button class="chat-widget-button" id="chatWidgetButton">
        💬
        <span class="chat-widget-badge">1</span>
      </button>

      <!-- Chat Window -->
      <div class="chat-widget-window" id="chatWidgetWindow">
        <div class="chat-widget-header">
          <div class="chat-widget-header-left">
            <div class="chat-widget-avatar">🤖</div>
            <div class="chat-widget-info">
              <h3>Я ассистент <a href="https://baltset.ru">электрика-калининград.рф</a></h3>
              <p>Помогу рассчитать стоимость</p>
            </div>
          </div>
          <button class="chat-widget-close" id="chatWidgetClose">✕</button>
        </div>
        <div class="chat-widget-body" id="chatWidgetBody"></div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', html);
  }

  attachEvents() {
    const button = document.getElementById('chatWidgetButton');
    const closeBtn = document.getElementById('chatWidgetClose');
    const window = document.getElementById('chatWidgetWindow');

    button.addEventListener('click', () => this.toggleChat());
    closeBtn.addEventListener('click', () => this.closeChat());

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.closeChat();
      }
    });
  }

  toggleChat() {
    this.isOpen = !this.isOpen;
    const window = document.getElementById('chatWidgetWindow');
    const badge = document.querySelector('.chat-widget-badge');
    
    if (this.isOpen) {
      window.classList.add('active');
      if (badge) badge.style.display = 'none';
    } else {
      window.classList.remove('active');
    }
  }

  closeChat() {
    this.isOpen = false;
    document.getElementById('chatWidgetWindow').classList.remove('active');
  }

  addBotMessage(text, inputType = null) {
    this.showTyping();
    setTimeout(() => {
      this.hideTyping();
      this.messages.push({
        type: 'bot',
        text,
        inputType,
        time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
      });
      this.render();
    }, 600);
  }

  addUserMessage(text) {
    this.messages.push({
      type: 'user',
      text,
      time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
    });
    this.render();
  }

  showTyping() {
    const body = document.getElementById('chatWidgetBody');
    const html = `
      <div class="chat-widget-message bot" id="typingIndicator">
        <div class="message-avatar-small">🤖</div>
        <div class="message-content">
          <div class="typing-indicator-widget">
            <div class="typing-dot-widget"></div>
            <div class="typing-dot-widget"></div>
            <div class="typing-dot-widget"></div>
          </div>
        </div>
      </div>
    `;
    body.insertAdjacentHTML('beforeend', html);
    body.scrollTop = body.scrollHeight;
  }

  hideTyping() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
  }

  render() {
    const body = document.getElementById('chatWidgetBody');
    
    body.innerHTML = this.messages.map((msg, i) => {
      if (msg.type === 'bot') {
        let html = `
          <div class="chat-widget-message bot">
            <div class="message-avatar-small">🤖</div>
            <div class="message-content">
              ${msg.text.replace(/\n/g, '<br>')}
              <div class="message-time">${msg.time}</div>
            </div>
          </div>
        `;

        if (i === this.messages.length - 1 && msg.inputType) {
          html += this.renderInput(msg.inputType);
        }

        return html;
      } else {
        return `
          <div class="chat-widget-message user">
            <div class="message-content">
              ${msg.text}
              <div class="message-time">${msg.time}</div>
            </div>
            <div class="message-avatar-small">👤</div>
          </div>
        `;
      }
    }).join('');

    setTimeout(() => {
      body.scrollTop = body.scrollHeight;
      const input = body.querySelector('.chat-widget-input');
      if (input) input.focus();
    }, 100);
  }

  renderInput(type) {
    switch(type) {
      case 'greeting-buttons':
        return `
          <div class="chat-widget-buttons">
            <button class="chat-widget-btn chat-widget-btn-primary" onclick="chatWidget.selectService('wiring')">
              ⚡ Провести электрику с нуля
            </button>
            <button class="chat-widget-btn chat-widget-btn-primary" onclick="chatWidget.selectService('installation')">
              🔧 Установить розетки/выключатели
            </button>
            <button class="chat-widget-btn" onclick="chatWidget.selectService('repair')">
              🔨 Ремонт/замена
            </button>
            <button class="chat-widget-btn" onclick="chatWidget.selectService('consultation')">
              💬 Консультация мастера
            </button>
          </div>
        `;

      case 'outlets-input':
        return `
          <div class="chat-widget-input-container">
            <input type="number" class="chat-widget-input" id="widgetInput" placeholder="Введите количество..." min="0" onkeypress="if(event.key==='Enter')chatWidget.submitNumber('outlets')">
            <button class="chat-widget-send" onclick="chatWidget.submitNumber('outlets')">✈️</button>
          </div>
        `;

      case 'switches-input':
        return `
          <div class="chat-widget-input-container">
            <input type="number" class="chat-widget-input" id="widgetInput" placeholder="Введите количество..." min="0" onkeypress="if(event.key==='Enter')chatWidget.submitNumber('switches')">
            <button class="chat-widget-send" onclick="chatWidget.submitNumber('switches')">✈️</button>
          </div>
        `;

      case 'lights-input':
        return `
          <div class="chat-widget-input-container">
            <input type="number" class="chat-widget-input" id="widgetInput" placeholder="Введите количество..." min="0" onkeypress="if(event.key==='Enter')chatWidget.submitNumber('lights')">
            <button class="chat-widget-send" onclick="chatWidget.submitNumber('lights')">✈️</button>
          </div>
        `;

      case 'phone-input':
        return `
          <div class="chat-widget-input-container">
            <input type="tel" class="chat-widget-input" id="widgetInput" placeholder="+7 (___) ___-__-__" onkeypress="if(event.key==='Enter')chatWidget.submitPhone()">
            <button class="chat-widget-send" onclick="chatWidget.submitPhone()">✈️</button>
          </div>
        `;

      default:
        return '';
    }
  }

  selectService(service) {
    const names = {
      'wiring': '⚡ Провести электрику с нуля',
      'installation': '🔧 Установить розетки/выключатели',
      'repair': '🔨 Ремонт/замена',
      'consultation': '💬 Консультация мастера'
    };

    this.addUserMessage(names[service]);
    this.data.service = service;

    if (service === 'wiring') {
      this.step = 'OUTLETS';
      this.addBotMessage('🔌 Сколько розеток планируете установить?', 'outlets-input');
    } else if (service === 'installation') {
      this.step = 'OUTLETS';
      this.addBotMessage('🔌 Сколько розеток нужно установить?', 'outlets-input');
    } else if (service === 'repair') {
      this.addBotMessage('🔧 Опишите что нужно отремонтировать или заменить.\n\nМастер свяжется с вами для уточнения деталей.', 'phone-input');
    } else if (service === 'consultation') {
      this.addBotMessage('💬 Отлично! Наш мастер ответит на все ваши вопросы.\n\nОставьте ваш номер телефона:', 'phone-input');
    }
  }

  submitNumber(field) {
    const input = document.getElementById('widgetInput');
    if (!input || !input.value) return;

    const value = parseInt(input.value);
    if (value < 0) return;

    this.addUserMessage(value + ' шт.');
    this.data[field] = value;

    if (field === 'outlets') {
      this.step = 'SWITCHES';
      this.addBotMessage('💡 Сколько выключателей?', 'switches-input');
    } else if (field === 'switches') {
      this.step = 'LIGHTS';
      this.addBotMessage('💡 Сколько светильников/люстр?', 'lights-input');
    } else if (field === 'lights') {
      this.step = 'PHONE';
      this.data.lights = value;
      this.calculateAndShow();
    }
  }

  calculateAndShow() {
    const outlets = this.data.outlets || 0;
    const switches = this.data.switches || 0;
    const lights = this.data.lights || 0;

    let total = 0;
    let breakdown = '';

    if (this.data.service === 'wiring') {
      total = (outlets * 500) + (switches * 400) + (lights * 1500);
      breakdown = `
📊 Расчёт:
🔌 ${outlets} розеток × 500₽ = ${outlets * 500}₽
💡 ${switches} выключателей × 400₽ = ${switches * 400}₽
💡 ${lights} светильников × 1500₽ = ${lights * 1500}₽

💰 ИТОГО: ${total.toLocaleString('ru-RU')} ₽
      `;
    } else {
      total = (outlets * 250) + (switches * 250) + (lights * 800);
      breakdown = `
📊 Расчёт:
🔌 ${outlets} розеток × 250₽ = ${outlets * 250}₽
💡 ${switches} выключателей × 250₽ = ${switches * 250}₽
💡 ${lights} светильников × 800₽ = ${lights * 800}₽

💰 ИТОГО: ${total.toLocaleString('ru-RU')} ₽
      `;
    }

    this.addBotMessage(breakdown);

    setTimeout(() => {
      this.addBotMessage('📱 Оставьте ваш номер телефона, и мастер свяжется с вами для уточнения деталей:', 'phone-input');
    }, 1000);
  }

  submitPhone() {
    const input = document.getElementById('widgetInput');
    if (!input || !input.value.trim()) return;

    const phone = input.value.trim();
    this.addUserMessage(phone);
    this.data.phone = phone;

    this.addBotMessage('✅ Отлично! Заявка принята.\n\n📞 Наш мастер свяжется с вами в течение 15 минут.\n\nСпасибо за обращение! 🙏');
    
    // Track in analytics
    if (typeof ym !== 'undefined') {
      ym(98765432, 'reachGoal', 'chat_widget_lead', {
        service: this.data.service,
        phone: this.data.phone
      });
    }
  }

  reset() {
    this.messages = [];
    this.step = 'GREETING';
    this.data = {};
    this.addBotMessage('👋 Здравствуйте! Я помогу рассчитать стоимость электромонтажных работ.\n\n💡 Что вас интересует?', 'greeting-buttons');
  }
}

// Initialize chat widget when DOM is ready
let chatWidget;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    chatWidget = new ChatWidget();
  });
} else {
  chatWidget = new ChatWidget();
}
