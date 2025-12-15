// Conversational AI-чат с воронкой (Telegram-стиль, UX по Дональду Норману)
// 2 сценария: Вызов мастера на осмотр | Рассчитать стоимость

class AIChat {
  constructor(calculator) {
    this.calculator = calculator;
    this.messages = [];
    this.step = 0;
    this.scenario = null;
    this.data = {};
    this.init();
  }

  init() {
    this.addBot('💰 Хорошо! Рассчитаем стоимость.\n\n❓ Что именно нужно оценить?\n\n<span style="font-size:11px;color:#999">чтобы точно рассчитать стоимость, ответьте на пару вопросов</span>', 'estimate-type');
    this.render();
  }

  // Сценарий 1: Вызов мастера
  startInspection() {
    this.scenario = 'inspection';
    this.step = 0;
    this.addBot('📅 Отлично! Запишу вас на бесплатный осмотр.\n\n🕐 Удобное время для визита?', 'time-select');
  }

  handleInspectionTime(time) {
    this.data.visitTime = time;
    this.addUser(time);
    this.addBot('✍️ Кратко опишите задачу\n\n<span style="font-size:11px;color:#999">например: установить розетку / сделать новую проводку в комнате</span>', 'text-input', 'taskDescription');
  }

  handleTaskDescription(text) {
    this.data.taskDescription = text;
    this.addUser(text);
    this.addBot('📍 Укажите адрес\n\n<span style="font-size:11px;color:#999">улица, дом, квартира, этаж, подъезд</span>', 'text-input', 'address');
  }

  handleAddress(text) {
    this.data.address = text;
    this.addUser(text);
    this.addBot('📅 Желаемая дата визита?', 'date-picker', 'desiredDate');
  }

  handleDate(date) {
    this.data.desiredDate = date;
    this.addUser(date);
    this.addBot('📞 Контактный телефон\n\n<span style="font-size:11px;color:#999">Укажите #тел. клиента</span>', 'phone-input', 'phone');
  }

  handlePhone(phone) {
    this.data.phone = phone;
    this.addUser(phone);
    this.addBot('📝 Остались пожелания к заявке?\n\n<span style="font-size:11px;color:#999">Подробно опишите суть и особенности проекта: сроки начала и завершения работ, особенности подъезда строительной техники, наличие подведенных коммуникаций, наличие чертежей и тд.</span>', 'textarea-input', 'additionalWishes');
  }

  handleWishes(text) {
    this.data.additionalWishes = text;
    this.addUser(text || 'Пожеланий нет');
    this.showInspectionResult();
  }

  showInspectionResult() {
    let summary = '✅ Заявка принята!\n\n';
    summary += `🕐 Время: ${this.data.visitTime}\n`;
    summary += `📍 Адрес: ${this.data.address}\n`;
    summary += `📅 Дата: ${this.data.desiredDate}\n`;
    summary += `📞 Телефон: ${this.data.phone}\n`;
    summary += `\n💬 Задача: ${this.data.taskDescription}`;
    
    this.addBot(summary);
    
    setTimeout(() => {
      this.addBot('✉️ Мастер свяжется с вами в ближайшее время!\n\nСпасибо за обращение! 😊');
    }, 1000);
  }

  // Сценарий 2: Расчёт стоимости
  startEstimate() {
    this.scenario = 'estimate';
    this.step = 0;
    this.addBot('💰 Хорошо! Рассчитаем стоимость.\n\n❓ Что именно нужно оценить?\n\n<span style="font-size:11px;color:#999">чтобы точно рассчитать стоимость, ответьте на пару вопросов</span>', 'estimate-type');
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
    this.addBot('❓ Что именно устанавливаем?\n\n👉 Вызов мастера, сборка рожковой люстры - 500 Р', 'device-type');
  }

  handleDeviceType(type) {
    this.data.deviceType = type;
    const names = {
      'light': 'Люстра / светильник - 1 500 ₽/шт',
      'outlet': 'Розетка / выключатель - 350 ₽/шт',
      'breaker': 'Автомат защиты (электрощит) - 1 000 ₽/шт',
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
    this.addBot('💡 Есть ли уже проводка?\n\n👉 Если проводки нет, её нужно будет подвести', 'wiring-check');
  }

  handleWiringCheck(hasWiring) {
    this.data.hasWiring = hasWiring;
    this.addUser(hasWiring === 'yes' ? 'Да, всё готово' : hasWiring === 'no' ? 'Нужно подвести провода' : 'Не знаю');
    this.showEstimateResult();
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
    this.fillCalculatorAndShow();
  }

  fillCalculatorAndShow() {
    this.addBot('📊 Рассчитываю...');
    
    setTimeout(() => {
      this.calculator.clearAll();
      
      const { outlets, switches, lights } = this.data;
      
      // Заполняем калькулятор
      const lightContainer = this.calculator.containers.find(c => c.id === 'chandelier');
      const switchContainer = this.calculator.containers.find(c => c.id === 'sw-install');
      const outletContainer = this.calculator.containers.find(c => c.id === 'out-install');
      
      if (lights > 0 && lightContainer) {
        const opt = lightContainer.options.find(o => o.id === 'install');
        if (opt) {
          opt.enabled = true;
          opt.quantity = lights;
        }
      }
      
      if (switches > 0 && switchContainer) {
        const opt = switchContainer.options.find(o => o.id === 'install');
        if (opt) {
          opt.enabled = true;
          opt.quantity = switches;
        }
      }
      
      if (outlets > 0 && outletContainer) {
        const opt = outletContainer.options.find(o => o.id === 'install');
        if (opt) {
          opt.enabled = true;
          opt.quantity = outlets;
        }
      }
      
      this.calculator.render();
      this.calculator.updateTotal();
      
      this.showEstimateResult();
    }, 800);
  }

  showEstimateResult() {
    const total = this.calculator.calculateGrandTotal();
    
    let summary = '✅ Готово!\n\n';
    
    if (this.data.outlets) {
      summary += `🔌 ${this.data.outlets} роз. • 💡 ${this.data.lights} свет. • 🎚️ ${this.data.switches} выкл.\n`;
    } else if (this.data.deviceType) {
      const names = {
        'light': 'Люстра/светильник',
        'outlet': 'Розетка/выключатель',
        'breaker': 'Автомат защиты'
      };
      summary += `${names[this.data.deviceType]}: ${this.data.deviceQuantity} шт.\n`;
    }
    
    summary += `\n💰 ИТОГО: ${this.calculator.formatPrice(total)} ₽`;
    
    this.addBot(summary);
    
    setTimeout(() => {
      const el = document.getElementById('calculator-container');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }, 500);
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
        <img src="https://i.ibb.co/9ZQY8Qm/denis-kostin.jpg" alt="Денис" class="message-avatar" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 2px solid #FFD700;">
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
            <img src="https://i.ibb.co/9ZQY8Qm/denis-kostin.jpg" alt="Денис" class="message-avatar" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 2px solid #FFD700;">
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
            <button class="chat-btn chat-btn-primary" onclick="aiChat.startInspection()">📅 Вызвать мастера на осмотр</button>
            <button class="chat-btn chat-btn-primary" onclick="aiChat.startEstimate()">💰 Рассчитать стоимость</button>
          </div>
        `;
      
      case 'time-select':
        return `
          <div class="chat-buttons">
            <button class="chat-btn" onclick="aiChat.handleInspectionTime('Утро (9:00-12:00)')">🌅 Утро (9:00-12:00)</button>
            <button class="chat-btn" onclick="aiChat.handleInspectionTime('День (12:00-17:00)')">☀️ День (12:00-17:00)</button>
            <button class="chat-btn" onclick="aiChat.handleInspectionTime('Вечер (17:00-20:00)')">🌆 Вечер (17:00-20:00)</button>
          </div>
        `;
      
      case 'text-input':
        return `
          <div class="chat-input-container">
            <input type="text" class="chat-input" placeholder="Введите текст..." id="chat-text-input" onkeypress="if(event.key==='Enter')aiChat.submitText('${field}')">
            <button class="chat-send-btn" onclick="aiChat.submitText('${field}')">✈️</button>
          </div>
        `;
      
      case 'textarea-input':
        return `
          <div class="chat-input-container" style="flex-direction:column;gap:12px">
            <textarea class="chat-textarea" placeholder="Опишите ваши пожелания..." id="chat-textarea-input" rows="4"></textarea>
            <button class="chat-btn chat-btn-primary" onclick="aiChat.submitTextarea('${field}')">Отправить</button>
          </div>
        `;
      
      case 'phone-input':
        return `
          <div class="chat-input-container">
            <input type="tel" class="chat-input" placeholder="+7 (___) ___-__-__" id="chat-phone-input" onkeypress="if(event.key==='Enter')aiChat.submitPhone('${field}')">
            <button class="chat-send-btn" onclick="aiChat.submitPhone('${field}')">✈️</button>
          </div>
        `;
      
      case 'date-picker':
        return `
          <div class="chat-input-container">
            <input type="date" class="chat-input" id="chat-date-input" min="${new Date().toISOString().split('T')[0]}">
            <button class="chat-send-btn" onclick="aiChat.submitDate('${field}')">✈️</button>
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
            <button class="chat-btn" onclick="aiChat.handleDeviceType('breaker')">⚡ Автомат защиты (электрощит) - 1 000 ₽/шт</button>
            <button class="chat-btn chat-btn-secondary" onclick="aiChat.handleDeviceType('multiple')">📦 Несколько устройств</button>
          </div>
        `;
      
      case 'wiring-check':
        return `
          <div class="chat-buttons">
            <button class="chat-btn" onclick="aiChat.handleWiringCheck('yes')">✅ Да, всё готово</button>
            <button class="chat-btn" onclick="aiChat.handleWiringCheck('no')">🔧 Нужно подвести провода</button>
            <button class="chat-btn chat-btn-secondary" onclick="aiChat.handleWiringCheck('unknown')">❓ Не знаю</button>
          </div>
        `;
      
      default:
        return '';
    }
  }

  submitText(field) {
    const input = document.getElementById('chat-text-input');
    if (!input || !input.value.trim()) return;
    
    const value = input.value.trim();
    input.value = '';
    
    if (field === 'taskDescription') this.handleTaskDescription(value);
    else if (field === 'address') this.handleAddress(value);
  }

  submitTextarea(field) {
    const input = document.getElementById('chat-textarea-input');
    const value = input ? input.value.trim() : '';
    
    if (field === 'additionalWishes') this.handleWishes(value);
  }

  submitPhone(field) {
    const input = document.getElementById('chat-phone-input');
    if (!input || !input.value.trim()) return;
    
    this.handlePhone(input.value.trim());
  }

  submitDate(field) {
    const input = document.getElementById('chat-date-input');
    if (!input || !input.value) return;
    
    const date = new Date(input.value);
    const formatted = date.toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' });
    
    this.handleDate(formatted);
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
    this.step = 0;
    this.scenario = null;
    this.data = {};
    this.init();
  }
}

let aiChat = null;
