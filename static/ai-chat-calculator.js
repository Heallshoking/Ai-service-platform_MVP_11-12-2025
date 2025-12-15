// AI-чат для калькулятора (упрощённая версия)

class AIChat {
  constructor(calculator) {
    this.calculator = calculator;
    this.messages = [];
    this.scenario = null;
    this.data = {};
    this.init();
  }

  init() {
    this.addBot('👋 Здравствуйте! Я помогу рассчитать стоимость электромонтажа.\n\n💡 Что вас интересует?', 'scenario-choice');
    this.render();
  }

  startEstimate() {
    this.scenario = 'estimate';
    this.addUser('Рассчитать стоимость');
    this.addBot('💰 Отлично! Рассчитаем стоимость.\n\n❓ Что именно нужно оценить?', 'estimate-type');
  }

  handleEstimateType(type) {
    this.data.estimateType = type;
    
    if (type === 'wiring') {
      this.addUser('Электромонтажные работы в квартире');
      this.askWiringQuestions();
    } else {
      this.addUser('Установка люстры, выключателя или розеток');
      this.askDeviceQuestions();
    }
  }

  askWiringQuestions() {
    this.addBot('🔌 Сколько розеток планируете?', 'number-input', 'outlets');
  }

  askDeviceQuestions() {
    this.addBot('❓ Что именно устанавливаем?', 'device-type');
  }

  handleDeviceType(type) {
    this.data.deviceType = type;
    const names = {
      'light': 'Люстра / светильник',
      'outlet': 'Розетка / выключатель',
      'multiple': 'Несколько устройств'
    };
    
    this.addUser(names[type]);
    
    if (type === 'multiple') {
      this.askWiringQuestions();
    } else {
      this.addBot('🔢 Сколько штук?', 'number-input', 'deviceQuantity');
    }
  }

  handleDeviceQuantity(qty) {
    this.data.deviceQuantity = qty;
    this.addUser(qty + ' шт.');
    this.showSimpleEstimate();
  }

  handleOutlets(qty) {
    this.data.outlets = qty;
    this.addUser(qty + ' розеток');
    this.addBot('💡 Сколько светильников?', 'number-input', 'lights');
  }

  handleLights(qty) {
    this.data.lights = qty;
    this.addUser(qty + ' светильников');
    this.addBot('🎚️ Сколько выключателей?', 'number-input', 'switches');
  }

  handleSwitches(qty) {
    this.data.switches = qty;
    this.addUser(qty + ' выключателей');
    this.showEstimateResult();
  }

  showSimpleEstimate() {
    const prices = {
      'light': 1500,
      'outlet': 350
    };
    
    const price = prices[this.data.deviceType] || 500;
    const total = price * (this.data.deviceQuantity || 1);
    
    let summary = '✅ Готово!\n\n';
    summary += `💰 ИТОГО: ${total.toLocaleString('ru-RU')} ₽`;
    
    this.addBot(summary);
    
    setTimeout(() => {
      this.addBot('📋 Используйте калькулятор ниже для более точного расчёта с учётом всех работ!');
    }, 800);
  }

  showEstimateResult() {
    const outlets = this.data.outlets || 0;
    const lights = this.data.lights || 0;
    const switches = this.data.switches || 0;
    
    const total = (outlets * 350) + (lights * 1500) + (switches * 350);
    
    let summary = '✅ Готово!\n\n';
    summary += `🔌 ${outlets} роз. • 💡 ${lights} свет. • 🎚️ ${switches} выкл.\n`;
    summary += `\n💰 ИТОГО: ${total.toLocaleString('ru-RU')} ₽`;
    
    this.addBot(summary);
    
    setTimeout(() => {
      this.addBot('📋 Для более точного расчёта используйте калькулятор ниже!');
      const el = document.querySelector('.container');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 800);
  }

  // Helpers
  addBot(text, inputType = null, field = null) {
    this.showTyping();
    setTimeout(() => {
      this.hideTyping();
      this.messages.push({
        type: 'bot',
        text,
        inputType,
        field,
        time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
      });
      this.render();
    }, 600);
  }

  addUser(text) {
    this.messages.push({
      type: 'user',
      text,
      time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
    });
    this.render();
  }

  showTyping() {
    const container = document.getElementById('ai-chat-messages');
    if (!container) return;
    
    const html = `
      <div class="chat-message bot-message" id="typing-indicator">
        <div class="message-avatar">🤖</div>
        <div class="message-bubble bot-bubble">
          <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    container.scrollTop = container.scrollHeight;
  }

  hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  render() {
    const container = document.getElementById('ai-chat-messages');
    if (!container) return;
    
    container.innerHTML = this.messages.map((msg, i) => {
      if (msg.type === 'bot') {
        let html = `
          <div class="chat-message bot-message">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble bot-bubble">
              <div class="message-text">${msg.text}</div>
              <div class="message-time">${msg.time}</div>
            </div>
          </div>
        `;
        
        if (i === this.messages.length - 1 && msg.inputType) {
          html += this.renderInput(msg.inputType, msg.field);
        }
        
        return html;
      } else {
        return `
          <div class="chat-message user-message">
            <div class="message-bubble user-bubble">
              <div class="message-text">${msg.text}</div>
              <div class="message-time">${msg.time}</div>
            </div>
            <div class="message-avatar">👤</div>
          </div>
        `;
      }
    }).join('');
    
    setTimeout(() => {
      container.scrollTop = container.scrollHeight;
      const input = container.querySelector('.chat-input, .chat-textarea');
      if (input) input.focus();
    }, 100);
  }

  renderInput(type, field) {
    switch(type) {
      case 'scenario-choice':
        return `
          <div class="chat-buttons">
            <button class="chat-btn chat-btn-primary" onclick="aiChat.startEstimate()">💰 Рассчитать стоимость</button>
          </div>
        `;
      
      case 'number-input':
        return `
          <div class="chat-input-container">
            <input type="number" class="chat-input" placeholder="Введите количество..." id="chat-number-input" min="1" onkeypress="if(event.key==='Enter')aiChat.submitNumber('${field}')">
            <button class="chat-send-btn" onclick="aiChat.submitNumber('${field}')">✈️</button>
          </div>
        `;
      
      case 'estimate-type':
        return `
          <div class="chat-buttons">
            <button class="chat-btn" onclick="aiChat.handleEstimateType('wiring')">⚡ Электромонтажные работы в квартире</button>
            <button class="chat-btn" onclick="aiChat.handleEstimateType('devices')">💡 Установка люстры, выключателя или розеток</button>
          </div>
        `;
      
      case 'device-type':
        return `
          <div class="chat-buttons">
            <button class="chat-btn" onclick="aiChat.handleDeviceType('light')">💡 Люстра / светильник - 1 500 ₽/шт</button>
            <button class="chat-btn" onclick="aiChat.handleDeviceType('outlet')">🔌 Розетка / выключатель - 350 ₽/шт</button>
            <button class="chat-btn chat-btn-secondary" onclick="aiChat.handleDeviceType('multiple')">📦 Несколько устройств</button>
          </div>
        `;
      
      default:
        return '';
    }
  }

  submitNumber(field) {
    const input = document.getElementById('chat-number-input');
    if (!input || !input.value) return;
    
    const value = parseInt(input.value);
    if (value < 1) return;
    
    if (field === 'outlets') this.handleOutlets(value);
    else if (field === 'lights') this.handleLights(value);
    else if (field === 'switches') this.handleSwitches(value);
    else if (field === 'deviceQuantity') this.handleDeviceQuantity(value);
  }

  reset() {
    this.messages = [];
    this.scenario = null;
    this.data = {};
    this.init();
  }
}

let aiChat = null;
