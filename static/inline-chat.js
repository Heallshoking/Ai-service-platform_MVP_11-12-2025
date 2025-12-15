// Inline Chat - Always visible input with fullscreen expansion

class InlineChat {
  constructor() {
    this.isFullscreen = false;
    this.messages = [];
    this.step = 'GREETING';
    this.data = {};
    this.init();
  }

  init() {
    this.injectHTML();
    this.attachEvents();
    this.addWelcomeMessage();
  }

  injectHTML() {
    const html = `
      <!-- Inline Chat Input (Always Visible) -->
      <div class="inline-chat-input">
        <div class="inline-chat-container">
          <div class="inline-burger-menu" onclick="portfolioMenu.toggle()">
            <div class="burger-line"></div>
            <div class="burger-line"></div>
            <div class="burger-line"></div>
          </div>
          <div class="inline-input-wrapper">
            <input 
              type="text" 
              class="inline-input" 
              id="inlineInput" 
              placeholder="Напишите что вам нужно... Например: Установить 5 розеток"
              readonly
              onclick="inlineChat.openFullscreen()"
            >
          </div>
          <a href="https://t.me/YOUR_TELEGRAM_USERNAME" target="_blank" class="telegram-button" title="Написать в Telegram">
            <svg class="telegram-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.67-.52.36-.99.53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.48 1.02-.73 4-1.74 6.68-2.88 8.03-3.44 3.82-1.59 4.61-1.87 5.13-1.87.11 0 .37.03.53.17.14.11.17.26.19.37.01.08.03.29.01.45z"/>
            </svg>
          </a>
        </div>
      </div>

      <!-- Portfolio Menu -->
      <div class="portfolio-overlay" id="portfolioOverlay" onclick="portfolioMenu.close()"></div>
      <div class="portfolio-menu" id="portfolioMenu">
        
        <!-- Hero Image -->
        <div class="portfolio-hero">
          <img src="kaliningrad-hero.jpg" alt="Калининград" class="portfolio-hero-image">
          <div class="portfolio-hero-overlay">
            <button class="portfolio-close-btn-hero" onclick="portfolioMenu.close()">✕</button>
          </div>
        </div>
        
        <!-- White Navigation Bar -->
        <div class="portfolio-hero-nav-bar">
          <nav class="portfolio-hero-nav">
            <a href="/" class="portfolio-hero-nav-item" title="Главная">
              <span>🏠</span>
            </a>
            <a href="/catalog.html" class="portfolio-hero-nav-item">
              <span>Услуги электрика</span>
              <span class="portfolio-hero-badge" id="selectedItemsBadge" style="display: none;">0</span>
            </a>
            <button class="portfolio-continue-btn" id="portfolioContinueBtn" style="display: none;" onclick="portfolioMenu.makeOrder()">
              Продолжить
            </button>
          </nav>
        </div>
        
        <div class="portfolio-nav" id="servicesContainer">
          <!-- Установить светильник -->
          <div class="service-container" data-service="light">
            <div class="service-header" onclick="portfolioMenu.toggleService('light')">
              <div class="service-icon light">💡</div>
              <div class="service-info">
                <h3>Установить светильник</h3>
                <p>Установка светильника / люстры</p>
              </div>
              <div class="service-toggle">▼</div>
            </div>
            <div class="service-items">
              <div class="service-item" data-item-id="light-install" data-price="1000" onclick="portfolioMenu.handleItemClick('light-install', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('light-install', event)"></div>
                  </div>
                  <div class="service-item-text">Установить светильник</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+1000₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('light-install', event)">-</button>
                    <div class="quantity-display" id="qty-light-install">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('light-install', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="light-remove" data-price="500" onclick="portfolioMenu.handleItemClick('light-remove', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('light-remove', event)"></div>
                  </div>
                  <div class="service-item-text">Демонтаж светильника</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('light-remove', event)">-</button>
                    <div class="quantity-display" id="qty-light-remove">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('light-remove', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="light-assembly" data-price="500" onclick="portfolioMenu.handleItemClick('light-assembly', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('light-assembly', event)"></div>
                  </div>
                  <div class="service-item-text">Сборка люстры</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('light-assembly', event)">-</button>
                    <div class="quantity-display" id="qty-light-assembly">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('light-assembly', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="light-crystal" data-price="1500" onclick="portfolioMenu.handleItemClick('light-crystal', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('light-crystal', event)"></div>
                  </div>
                  <div class="service-item-text">Подвес хрусталя</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+1500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('light-crystal', event)">-</button>
                    <div class="quantity-display" id="qty-light-crystal">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('light-crystal', event)">+</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Установить выключатель -->
          <div class="service-container" data-service="switch">
            <div class="service-header" onclick="portfolioMenu.toggleService('switch')">
              <div class="service-icon switch">🔆</div>
              <div class="service-info">
                <h3>Установить выключатель</h3>
                <p>Установка выключателя, ремонт</p>
              </div>
              <div class="service-toggle">▼</div>
            </div>
            <div class="service-items">
              <div class="service-item" data-item-id="switch-move" data-price="1500" onclick="portfolioMenu.handleItemClick('switch-move', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('switch-move', event)"></div>
                  </div>
                  <div class="service-item-text">Добавить / перенести</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+1500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('switch-move', event)">-</button>
                    <div class="quantity-display" id="qty-switch-move">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('switch-move', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="switch-repair" data-price="1500" onclick="portfolioMenu.handleItemClick('switch-repair', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('switch-repair', event)"></div>
                  </div>
                  <div class="service-item-text">Ремонт с материалами</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+1500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('switch-repair', event)">-</button>
                    <div class="quantity-display" id="qty-switch-repair">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('switch-repair', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="switch-replace" data-price="350" onclick="portfolioMenu.handleItemClick('switch-replace', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('switch-replace', event)"></div>
                  </div>
                  <div class="service-item-text">Заменить выключатель</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+350₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('switch-replace', event)">-</button>
                    <div class="quantity-display" id="qty-switch-replace">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('switch-replace', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="switch-install" data-price="250" onclick="portfolioMenu.handleItemClick('switch-install', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('switch-install', event)"></div>
                  </div>
                  <div class="service-item-text">Установить выключатель</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+250₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('switch-install', event)">-</button>
                    <div class="quantity-display" id="qty-switch-install">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('switch-install', event)">+</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Установить розетку -->
          <div class="service-container" data-service="outlet">
            <div class="service-header" onclick="portfolioMenu.toggleService('outlet')">
              <div class="service-icon outlet">🔌</div>
              <div class="service-info">
                <h3>Установить розетку</h3>
                <p>Установка розеток, ремонт</p>
              </div>
              <div class="service-toggle">▼</div>
            </div>
            <div class="service-items">
              <div class="service-item" data-item-id="outlet-repair" data-price="1500" onclick="portfolioMenu.handleItemClick('outlet-repair', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('outlet-repair', event)"></div>
                  </div>
                  <div class="service-item-text">Ремонт с материалами</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+1500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('outlet-repair', event)">-</button>
                    <div class="quantity-display" id="qty-outlet-repair">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('outlet-repair', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="outlet-surface" data-price="500" onclick="portfolioMenu.handleItemClick('outlet-surface', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('outlet-surface', event)"></div>
                  </div>
                  <div class="service-item-text">Накладная розетка</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+500₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('outlet-surface', event)">-</button>
                    <div class="quantity-display" id="qty-outlet-surface">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('outlet-surface', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="outlet-replace" data-price="350" onclick="portfolioMenu.handleItemClick('outlet-replace', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('outlet-replace', event)"></div>
                  </div>
                  <div class="service-item-text">Заменить розетку</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+350₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('outlet-replace', event)">-</button>
                    <div class="quantity-display" id="qty-outlet-replace">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('outlet-replace', event)">+</button>
                  </div>
                </div>
              </div>
              <div class="service-item" data-item-id="outlet-install" data-price="250" onclick="portfolioMenu.handleItemClick('outlet-install', event)">
                <div class="service-item-left">
                  <div class="service-checkbox-wrapper">
                    <div class="service-checkbox" onclick="portfolioMenu.toggleCheckbox('outlet-install', event)"></div>
                  </div>
                  <div class="service-item-text">Установить розетку</div>
                </div>
                <div class="service-item-right">
                  <div class="service-price">+250₽</div>
                  <div class="quantity-controls">
                    <button class="quantity-btn minus" onclick="portfolioMenu.decreaseItem('outlet-install', event)">-</button>
                    <div class="quantity-display" id="qty-outlet-install">1</div>
                    <button class="quantity-btn plus" onclick="portfolioMenu.increaseItem('outlet-install', event)">+</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- AI Smart Notification -->
          <div class="ai-notification" id="aiNotification" style="display: none;">
            <div class="ai-notification-icon">🤖</div>
            <div class="ai-notification-content">
              <div class="ai-notification-text" id="aiNotificationText"></div>
            </div>
          </div>
        </div>
        <div class="portfolio-footer">
          <div class="portfolio-master-fee">
            <div class="portfolio-master-fee-label">
              <span>👨‍🔧</span>
              <span>Вызов мастера (включено)</span>
            </div>
            <div class="portfolio-master-fee-amount">+500₽</div>
          </div>
          <div class="portfolio-total">
            <div class="portfolio-total-label">ИТОГО:</div>
            <div class="portfolio-total-amount" id="portfolioTotalAmount">500 ₽</div>
          </div>
          <button class="portfolio-action-btn" id="portfolioOrderBtn" onclick="portfolioMenu.makeOrder()" style="display: none;">
            Продолжить
          </button>
        </div>
      </div>

      <!-- Fullscreen Chat -->
      <div class="fullscreen-chat" id="fullscreenChat">
        <div class="fullscreen-chat-header">
          <div class="fullscreen-chat-header-left">
            <div class="fullscreen-avatar">🤖</div>
            <div class="fullscreen-chat-info">
              <h2>Я ассистент <a href="https://baltset.ru">электрика-калининград.рф</a></h2>
              <p>Помогу рассчитать стоимость и вызвать мастера</p>
            </div>
          </div>
          <button class="fullscreen-close" onclick="inlineChat.closeFullscreen()">✕</button>
        </div>
        <div class="fullscreen-chat-body" id="fullscreenChatBody"></div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', html);
  }

  attachEvents() {
    // Close on ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isFullscreen) {
        this.closeFullscreen();
      }
    });
  }

  openFullscreen() {
    this.isFullscreen = true;
    document.getElementById('fullscreenChat').classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Scroll to bottom
    setTimeout(() => {
      const body = document.getElementById('fullscreenChatBody');
      body.scrollTop = body.scrollHeight;
    }, 100);
  }

  closeFullscreen() {
    this.isFullscreen = false;
    document.getElementById('fullscreenChat').classList.remove('active');
    document.body.style.overflow = '';
  }

  addWelcomeMessage() {
    this.addBotMessage(
      '👋 Здравствуйте! Я помогу вам быстро рассчитать стоимость работ или вызвать мастера.\n\n💡 Выберите что вам нужно:',
      'quick-actions'
    );
  }

  addBotMessage(text, inputType = null) {
    this.messages.push({
      type: 'bot',
      text,
      inputType,
      time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
    });
    this.render();
  }

  addUserMessage(text) {
    this.messages.push({
      type: 'user',
      text,
      time: new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
    });
    this.render();
  }

  render() {
    const body = document.getElementById('fullscreenChatBody');
    
    body.innerHTML = this.messages.map((msg, i) => {
      if (msg.type === 'bot') {
        let html = `
          <div class="fullscreen-message bot">
            <div class="fullscreen-message-avatar">🤖</div>
            <div class="fullscreen-message-content">
              ${msg.text.replace(/\n/g, '<br>')}
            </div>
          </div>
        `;

        if (i === this.messages.length - 1 && msg.inputType) {
          html += this.renderInput(msg.inputType);
        }

        return html;
      } else {
        return `
          <div class="fullscreen-message user">
            <div class="fullscreen-message-content">
              ${msg.text}
            </div>
            <div class="fullscreen-message-avatar">👤</div>
          </div>
        `;
      }
    }).join('');

    setTimeout(() => {
      body.scrollTop = body.scrollHeight;
      const input = body.querySelector('.number-input');
      if (input) input.focus();
    }, 100);
  }

  renderInput(type) {
    switch(type) {
      case 'quick-actions':
        return `
          <div class="quick-actions">
            <button class="quick-action-btn primary" onclick="inlineChat.selectAction('calculate')">
              <div class="icon">💰</div>
              <div>Рассчитать стоимость</div>
            </button>
            <button class="quick-action-btn primary" onclick="inlineChat.selectAction('call-master')">
              <div class="icon">👨‍🔧</div>
              <div>Вызвать мастера</div>
            </button>
          </div>
        `;

      case 'service-type':
        return `
          <div class="chat-input-buttons">
            <button class="chat-input-btn" onclick="inlineChat.selectService('wiring')">
              ⚡ Провести электрику с нуля (от 5 000₽)
            </button>
            <button class="chat-input-btn" onclick="inlineChat.selectService('installation')">
              🔧 Установить розетки/выключатели (от 250₽/шт)
            </button>
            <button class="chat-input-btn" onclick="inlineChat.selectService('light')">
              💡 Установить светильники (от 800₽/шт)
            </button>
            <button class="chat-input-btn" onclick="inlineChat.selectService('repair')">
              🔨 Ремонт/замена оборудования
            </button>
          </div>
        `;

      case 'outlets-input':
        return `
          <div class="number-input-group">
            <input 
              type="number" 
              class="number-input" 
              id="numberInput" 
              placeholder="Введите количество..." 
              min="0"
              onkeypress="if(event.key==='Enter')inlineChat.submitNumber('outlets')"
            >
            <button class="number-submit-btn" onclick="inlineChat.submitNumber('outlets')">
              Далее →
            </button>
          </div>
        `;

      case 'switches-input':
        return `
          <div class="number-input-group">
            <input 
              type="number" 
              class="number-input" 
              id="numberInput" 
              placeholder="Введите количество..." 
              min="0"
              onkeypress="if(event.key==='Enter')inlineChat.submitNumber('switches')"
            >
            <button class="number-submit-btn" onclick="inlineChat.submitNumber('switches')">
              Далее →
            </button>
          </div>
        `;

      case 'lights-input':
        return `
          <div class="number-input-group">
            <input 
              type="number" 
              class="number-input" 
              id="numberInput" 
              placeholder="Введите количество..." 
              min="0"
              onkeypress="if(event.key==='Enter')inlineChat.submitNumber('lights')"
            >
            <button class="number-submit-btn" onclick="inlineChat.submitNumber('lights')">
              Рассчитать →
            </button>
          </div>
        `;

      case 'phone-input':
        return `
          <div class="number-input-group">
            <input 
              type="tel" 
              class="number-input" 
              id="numberInput" 
              placeholder="+7 (___) ___-__-__"
              onkeypress="if(event.key==='Enter')inlineChat.submitPhone()"
            >
            <button class="number-submit-btn" onclick="inlineChat.submitPhone()">
              Отправить
            </button>
          </div>
        `;

      default:
        return '';
    }
  }

  selectAction(action) {
    if (action === 'calculate') {
      this.addUserMessage('💰 Рассчитать стоимость');
      this.step = 'SERVICE_TYPE';
      this.addBotMessage('Отлично! Что именно нужно сделать?', 'service-type');
    } else if (action === 'call-master') {
      this.addUserMessage('👨‍🔧 Вызвать мастера');
      this.step = 'PHONE';
      this.addBotMessage(
        '✅ Мастер приедет в удобное время!\n\n🎁 Бесплатный осмотр и консультация\n\n📱 Оставьте ваш номер телефона:',
        'phone-input'
      );
    }
  }

  selectService(service) {
    const names = {
      'wiring': '⚡ Провести электрику с нуля',
      'installation': '🔧 Установить розетки/выключатели',
      'light': '💡 Установить светильники',
      'repair': '🔨 Ремонт/замена оборудования'
    };

    this.addUserMessage(names[service]);
    this.data.service = service;

    if (service === 'wiring') {
      this.step = 'OUTLETS';
      this.addBotMessage('🔌 Сколько розеток планируете? (можно 0)', 'outlets-input');
    } else if (service === 'installation') {
      this.step = 'OUTLETS';
      this.addBotMessage('🔌 Сколько розеток нужно установить?', 'outlets-input');
    } else if (service === 'light') {
      this.step = 'LIGHTS';
      this.addBotMessage('💡 Сколько светильников/люстр?', 'lights-input');
    } else if (service === 'repair') {
      this.step = 'PHONE';
      this.addBotMessage(
        '🔧 Мастер свяжется с вами для уточнения деталей.\n\n📱 Ваш номер телефона:',
        'phone-input'
      );
    }
  }

  submitNumber(field) {
    const input = document.getElementById('numberInput');
    if (!input) return;

    const value = parseInt(input.value) || 0;
    
    this.addUserMessage(value + ' шт.');
    this.data[field] = value;

    if (field === 'outlets') {
      this.step = 'SWITCHES';
      this.addBotMessage('💡 Сколько выключателей? (можно 0)', 'switches-input');
    } else if (field === 'switches') {
      this.step = 'LIGHTS';
      this.addBotMessage('💡 Сколько светильников/люстр? (можно 0)', 'lights-input');
    } else if (field === 'lights') {
      this.data.lights = value;
      this.calculatePrice();
    }
  }

  calculatePrice() {
    const outlets = this.data.outlets || 0;
    const switches = this.data.switches || 0;
    const lights = this.data.lights || 0;

    let total = 0;
    let breakdown = '';

    if (this.data.service === 'wiring') {
      total = (outlets * 500) + (switches * 400) + (lights * 1500);
      breakdown = `
📊 <b>Расчёт стоимости:</b>

🔌 ${outlets} розеток × 500₽ = <b>${(outlets * 500).toLocaleString('ru-RU')}₽</b>
💡 ${switches} выключателей × 400₽ = <b>${(switches * 400).toLocaleString('ru-RU')}₽</b>
💡 ${lights} светильников × 1500₽ = <b>${(lights * 1500).toLocaleString('ru-RU')}₽</b>

━━━━━━━━━━━━━━━━
💰 <b>ИТОГО: ${total.toLocaleString('ru-RU')} ₽</b>
      `;
    } else if (this.data.service === 'installation') {
      total = (outlets * 250) + (switches * 250) + (lights * 800);
      breakdown = `
📊 <b>Расчёт стоимости:</b>

🔌 ${outlets} розеток × 250₽ = <b>${(outlets * 250).toLocaleString('ru-RU')}₽</b>
💡 ${switches} выключателей × 250₽ = <b>${(switches * 250).toLocaleString('ru-RU')}₽</b>
💡 ${lights} светильников × 800₽ = <b>${(lights * 800).toLocaleString('ru-RU')}₽</b>

━━━━━━━━━━━━━━━━
💰 <b>ИТОГО: ${total.toLocaleString('ru-RU')} ₽</b>
      `;
    } else if (this.data.service === 'light') {
      total = lights * 800;
      breakdown = `
📊 <b>Расчёт стоимости:</b>

💡 ${lights} светильников × 800₽ = <b>${total.toLocaleString('ru-RU')}₽</b>
      `;
    }

    this.addBotMessage(breakdown);

    setTimeout(() => {
      this.step = 'PHONE';
      this.addBotMessage(
        '✅ Отлично! Хотите оформить заказ?\n\n📱 Оставьте ваш номер телефона и мастер свяжется с вами:',
        'phone-input'
      );
    }, 800);
  }

  submitPhone() {
    const input = document.getElementById('numberInput');
    if (!input || !input.value.trim()) return;

    const phone = input.value.trim();
    this.addUserMessage(phone);
    this.data.phone = phone;

    this.addBotMessage(
      '✅ <b>Заявка принята!</b>\n\n📞 Наш мастер свяжется с вами в течение 15 минут.\n\n🎁 Бесплатная консультация и осмотр\n\nСпасибо за обращение! 🙏'
    );

    // Track in analytics
    if (typeof ym !== 'undefined') {
      ym(98765432, 'reachGoal', 'inline_chat_lead', {
        service: this.data.service,
        total: this.calculateTotal(),
        phone: phone
      });
    }

    // Auto close after 3 seconds
    setTimeout(() => {
      this.reset();
    }, 5000);
  }

  calculateTotal() {
    const outlets = this.data.outlets || 0;
    const switches = this.data.switches || 0;
    const lights = this.data.lights || 0;

    if (this.data.service === 'wiring') {
      return (outlets * 500) + (switches * 400) + (lights * 1500);
    } else if (this.data.service === 'installation') {
      return (outlets * 250) + (switches * 250) + (lights * 800);
    } else if (this.data.service === 'light') {
      return lights * 800;
    }
    return 0;
  }

  reset() {
    this.closeFullscreen();
    this.messages = [];
    this.step = 'GREETING';
    this.data = {};
    this.addWelcomeMessage();
  }
}

// Portfolio Menu Controller
class PortfolioMenu {
  constructor() {
    this.isOpen = false;
    this.items = {};
    this.masterFee = 500; // Вызов мастера всегда включён
    this.total = this.masterFee;
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.isOpen = true;
    document.getElementById('portfolioMenu').classList.add('active');
    document.getElementById('portfolioOverlay').classList.add('active');
    document.querySelector('.inline-burger-menu').classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  close() {
    this.isOpen = false;
    document.getElementById('portfolioMenu').classList.remove('active');
    document.getElementById('portfolioOverlay').classList.remove('active');
    document.querySelector('.inline-burger-menu').classList.remove('active');
    document.body.style.overflow = '';
  }

  toggleService(serviceId) {
    const container = document.querySelector(`.service-container[data-service="${serviceId}"]`);
    if (container) {
      container.classList.toggle('expanded');
    }
  }

  // Клик на любую часть элемента (кроме кнопок)
  handleItemClick(itemId, event) {
    // Игнорируем клики на кнопки
    if (event.target.closest('.quantity-btn') || event.target.closest('.service-checkbox')) {
      return;
    }
    
    // Если услуга уже выбрана и количество = 1, то удаляем
    if (this.items[itemId] && this.items[itemId].quantity === 1) {
      this.removeItem(itemId);
    } else if (!this.items[itemId]) {
      // Если услуга не выбрана - добавляем
      this.addItem(itemId);
    }
  }

  // Добавление услуги
  addItem(itemId) {
    const serviceItem = document.querySelector(`[data-item-id="${itemId}"]`);
    const checkbox = serviceItem.querySelector('.service-checkbox');
    const controls = serviceItem.querySelector('.quantity-controls');
    const price = parseInt(serviceItem.dataset.price);
    const text = serviceItem.querySelector('.service-item-text').textContent;
    
    this.items[itemId] = {
      quantity: 1,
      price: price,
      text: text
    };
    
    checkbox.classList.add('checked');
    controls.classList.add('active');
    serviceItem.classList.add('selected');
    
    // Обновляем фон контейнера
    this.updateContainerBackground(serviceItem);
    
    this.updateTotal();
  }

  // Toggle чекбокса
  toggleCheckbox(itemId, event) {
    event.stopPropagation();
    
    if (!this.items[itemId]) {
      this.addItem(itemId);
    } else {
      this.removeItem(itemId);
    }
  }

  // Удаление услуги
  removeItem(itemId) {
    const serviceItem = document.querySelector(`[data-item-id="${itemId}"]`);
    const checkbox = serviceItem.querySelector('.service-checkbox');
    const controls = serviceItem.querySelector('.quantity-controls');
    
    delete this.items[itemId];
    checkbox.classList.remove('checked');
    controls.classList.remove('active');
    serviceItem.classList.remove('selected');
    
    // Сбрасываем количество на 1
    const qtyDisplay = document.getElementById(`qty-${itemId}`);
    if (qtyDisplay) qtyDisplay.textContent = '1';
    
    // Обновляем фон контейнера
    this.updateContainerBackground(serviceItem);
    
    this.updateTotal();
  }

  // Обновление фона контейнера
  updateContainerBackground(serviceItem) {
    const container = serviceItem.closest('.service-container');
    if (!container) return;
    
    // Проверяем есть ли выбранные услуги в этом контейнере
    const serviceId = container.dataset.service;
    const hasSelected = Array.from(container.querySelectorAll('.service-item')).some(item => {
      const itemId = item.dataset.itemId;
      return this.items[itemId];
    });
    
    if (hasSelected) {
      container.classList.add('has-selected');
    } else {
      container.classList.remove('has-selected');
    }
  }

  increaseItem(itemId, event) {
    event.stopPropagation();
    
    if (this.items[itemId]) {
      this.items[itemId].quantity++;
      this.updateQuantityDisplay(itemId);
      this.updateTotal();
    }
  }

  decreaseItem(itemId, event) {
    event.stopPropagation();
    
    if (this.items[itemId]) {
      if (this.items[itemId].quantity > 1) {
        // Уменьшаем количество
        this.items[itemId].quantity--;
        this.updateQuantityDisplay(itemId);
      } else {
        // Удаляем из корзины полностью
        this.removeItem(itemId);
      }
      this.updateTotal();
    }
  }

  updateQuantityDisplay(itemId) {
    const qtyElement = document.getElementById(`qty-${itemId}`);
    if (qtyElement && this.items[itemId]) {
      qtyElement.textContent = this.items[itemId].quantity;
    }
  }

  updateTotal() {
    let servicesTotal = 0;
    
    for (let itemId in this.items) {
      const item = this.items[itemId];
      servicesTotal += item.price * item.quantity;
    }
    
    this.total = servicesTotal + this.masterFee;
    
    const totalEl = document.getElementById('portfolioTotalAmount');
    const orderBtn = document.getElementById('portfolioOrderBtn');
    const continueBtn = document.getElementById('portfolioContinueBtn');
    const badgeEl = document.getElementById('selectedItemsBadge');
    const aiNotification = document.getElementById('aiNotification');
    const aiText = document.getElementById('aiNotificationText');
    
    if (totalEl) {
      totalEl.textContent = this.total.toLocaleString('ru-RU') + ' ₽';
    }
    
    // Обновляем счётчик выбранных услуг
    if (badgeEl) {
      const count = Object.keys(this.items).length;
      badgeEl.textContent = count;
      badgeEl.style.display = count > 0 ? 'inline-block' : 'none';
    }
    
    // Управление кнопкой "Продолжить"
    if (continueBtn) {
      const count = Object.keys(this.items).length;
      
      // Показываем кнопку только если есть выбранные услуги кроме вызова мастера
      if (count > 0 && !(count === 1 && this.items['master-call'])) {
        continueBtn.style.display = 'block';
      } else {
        continueBtn.style.display = 'none';
      }
    }
    
    // AI уведомление
    if (aiNotification && aiText) {
      const count = Object.keys(this.items).length;
      
      if (count > 0) {
        const messages = [
          `Отличный выбор! Вы выбрали ${count} услуг${count > 1 ? 'и' : 'у'} на сумму ${servicesTotal.toLocaleString('ru-RU')}₽. С вызовом мастера получается ${this.total.toLocaleString('ru-RU')}₽. Нажмите "Продолжить" для оформления!`,
          `Выбрано ${count} услуг${count > 1 ? '' : 'а'}. Мастер приедет, оценит объём и назовёт точную стоимость. Предварительно: ~${this.total.toLocaleString('ru-RU')}₽`,
          `У вас в корзине ${count} позици${count > 1 ? 'и' : 'я'}. Мы свяжемся с вами в течение 15 минут и уточним детали!`
        ];
        
        // Выбираем случайное сообщение
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        aiText.textContent = randomMessage;
        aiNotification.style.display = 'flex';
      } else {
        aiNotification.style.display = 'none';
      }
    }
    
    // Кнопка всегда активна (минимум вызов мастера)
    if (orderBtn) {
      orderBtn.disabled = false;
    }
  }

  makeOrder() {
    // Собираем данные заказа
    const orderLines = [];
    
    // Добавляем вызов мастера
    orderLines.push(`👨‍🔧 Вызов мастера = ${this.masterFee.toLocaleString('ru-RU')} ₽`);
    
    // Добавляем выбранные услуги
    for (let itemId in this.items) {
      const item = this.items[itemId];
      orderLines.push(`${item.text} x${item.quantity} = ${(item.price * item.quantity).toLocaleString('ru-RU')} ₽`);
    }
    
    const orderSummary = orderLines.join('\n');
    const hasServices = Object.keys(this.items).length > 0;
    
    // Закрываем portfolio и открываем чат
    this.close();
    inlineChat.openFullscreen();
    
    // Добавляем предзаполненные данные в чат
    inlineChat.addUserMessage('Заказ услуг:\n' + orderSummary);
    
    const message = hasServices
      ? `✅ Отлично! Вы выбрали услуги на сумму ${this.total.toLocaleString('ru-RU')} ₽\n\n📱 Оставьте ваш номер телефона и мастер свяжется с вами:`
      : `👨‍🔧 Вызов мастера на дом - ${this.masterFee.toLocaleString('ru-RU')} ₽

Мастер приедет, оценит объём работ и назовёт точную стоимость.

📱 Оставьте ваш номер телефона:`;
    
    inlineChat.addBotMessage(message, 'phone-input');
    inlineChat.step = 'PHONE';
    inlineChat.data.selectedServices = this.items;
    inlineChat.data.masterFee = this.masterFee;
    inlineChat.data.total = this.total;
    
    // Track in analytics
    if (typeof ym !== 'undefined') {
      ym(98765432, 'reachGoal', 'portfolio_services_selected', {
        total: this.total,
        count: Object.keys(this.items).length,
        hasMasterFee: true
      });
    }
  }

  reset() {
    this.items = {};
    this.total = this.masterFee;
    
    // Сбрасываем все чекбоксы и контролы
    document.querySelectorAll('.service-checkbox.checked').forEach(checkbox => {
      checkbox.classList.remove('checked');
    });
    
    document.querySelectorAll('.quantity-controls.active').forEach(controls => {
      controls.classList.remove('active');
    });
    
    document.querySelectorAll('.service-item.selected').forEach(item => {
      item.classList.remove('selected');
    });
    
    document.querySelectorAll('.service-container.has-selected').forEach(container => {
      container.classList.remove('has-selected');
    });
    
    // Сбрасываем количество на 1
    document.querySelectorAll('.quantity-display').forEach(display => {
      display.textContent = '1';
    });
    
    // Сворачиваем все контейнеры
    document.querySelectorAll('.service-container.expanded').forEach(container => {
      container.classList.remove('expanded');
    });
    
    this.updateTotal();
  }
}

// Initialize
let inlineChat, portfolioMenu;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    inlineChat = new InlineChat();
    portfolioMenu = new PortfolioMenu();
    
    // Close portfolio menu on ESC
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && portfolioMenu.isOpen) {
        portfolioMenu.close();
      }
    });
  });
} else {
  inlineChat = new InlineChat();
  portfolioMenu = new PortfolioMenu();
  
  // Close portfolio menu on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && portfolioMenu.isOpen) {
      portfolioMenu.close();
    }
  });
}
