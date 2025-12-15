// Полная копия функционала услуги-электрика.org/products
// Автоматический расчет кабеля, система скидок, все как в reference

class ElectricalCalculator {
  constructor() {
    this.containers = this.getInitialContainers();
    this.init();
  }
  
  getInitialContainers() {
    return [
      {
        id: 'chandelier',
        name: 'Установить светильник',
        description: 'Установка светильника / люстры',
        icon: '💡',
        color: 'amber',
        section: 'services',
        expanded: false,
        options: [
          { id: 'install', name: 'Установить светильник', price: 1000, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'dismantle', name: 'Демонтаж светильника', price: 500, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'assemble', name: 'Сборка люстры', price: 500, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'crystal', name: 'Подвес хрусталя — 1 час', price: 1500, quantity: 1, enabled: false }
        ]
      },
      {
        id: 'sw-install',
        name: 'Установить выключатель',
        description: 'Установка выключателя, ремонт',
        icon: '🎚️',
        color: 'blue',
        section: 'services',
        expanded: false,
        options: [
          { id: 'move-switch-alt', name: 'Добавить выключатель или перенести розетку в другое место', price: 1500, quantity: 1, enabled: false },
          { id: 'repair', name: 'Ремонт с учётом материалов', price: 1500, quantity: 1, enabled: false, discount: { minQty: 10, percent: 15 } },
          { id: 'replace-switch', name: 'Заменить выключатель', price: 350, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'install', name: 'Установить выключатель', price: 250, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } }
        ]
      },
      {
        id: 'out-install',
        name: 'Установить розетку',
        description: 'Установка розеток, ремонт',
        icon: '🔌',
        color: 'green',
        section: 'services',
        expanded: false,
        options: [
          { id: 'repair', name: 'Ремонт с учётом материалов', price: 1500, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'surface-outlet', name: 'Накладная розетка', price: 500, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'replace-outlet', name: 'Заменить розетку', price: 350, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } },
          { id: 'install', name: 'Установить розетку', price: 250, quantity: 1, enabled: false, discount: { minQty: 5, percent: 10 } }
        ]
      },
      {
        id: 'wiring-complex',
        name: 'Электромонтажные работы',
        description: 'Черновые работы со штроблением, сверлением и установкой подрозетника, комплексная замена проводки в Калининграде',
        icon: '⚡',
        color: 'amber',
        section: 'wiring',
        expanded: true,
        options: [
          { id: 'add-outlet', name: 'Добавить розетку', price: 850, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'breaker-install', name: 'Установка автомата защиты', price: 1000, quantity: 1, enabled: false, discount: { minQty: 10, percent: 50 }, noCable: true },
          { id: 'block-2', name: 'Блок из 2-х розеток', price: 1200, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'move-switch', name: 'Добавить выключатель или перенести розетку в другое место', price: 1500, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'block-3', name: 'Блок из 3-х розеток', price: 2500, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'box-surface', name: 'Бокс открытого монтажа', price: 2500, quantity: 1, enabled: false, noAutoDiscount: true, noCable: true },
          { id: 'input-cable', name: 'Новый вводной кабель', price: 2500, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'block-4', name: 'Блок из 4-х розеток', price: 3000, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'breaker-replace', name: 'Замена автомата с учётом материала', price: 3000, quantity: 1, enabled: false, noCable: true },
          { id: 'gas-sensor', name: 'Перенос газовых детекторов', price: 3500, quantity: 1, enabled: false, noAutoDiscount: true },
          { id: 'meter', name: 'Установка электросчётчика 220V', price: 3500, quantity: 1, enabled: false, noAutoDiscount: true, noCable: true },
          { id: 'box-flush', name: 'Бокс скрытого монтажа', price: 8000, quantity: 1, enabled: false, noAutoDiscount: true, noCable: true },
          { id: 'block-5', name: 'Блок из 5 розеток +закладная', price: 8000, quantity: 1, enabled: false, noAutoDiscount: true }
        ]
      }
    ];
  }
  
  toggleContainer(containerId) {
    const container = this.containers.find(c => c.id === containerId);
    if (container) {
      container.expanded = !container.expanded;
      this.render();
    }
  }
  
  toggleOption(containerId, optionId) {
    const container = this.containers.find(c => c.id === containerId);
    const option = container.options.find(o => o.id === optionId);
    
    option.enabled = !option.enabled;
    if (!option.enabled) {
      option.quantity = 1;
    }
    
    this.render();
    this.updateTotal();
  }
  
  updateQuantity(containerId, optionId, delta) {
    const container = this.containers.find(c => c.id === containerId);
    const option = container.options.find(o => o.id === optionId);
    
    const newQuantity = option.quantity + delta;
    if (newQuantity < 1) {
      option.enabled = false;
      option.quantity = 1;
    } else {
      option.quantity = newQuantity;
    }
    
    this.render();
    this.updateTotal();
  }
  
  calculateOptionPrice(option) {
    if (!option.enabled) return 0;
    
    let price = option.price * option.quantity;
    
    if (option.discount && option.quantity >= option.discount.minQty) {
      price = price * (1 - option.discount.percent / 100);
    }
    
    return price;
  }
  
  calculateContainerTotal(container) {
    return container.options.reduce((sum, opt) => sum + this.calculateOptionPrice(opt), 0);
  }
  
  calculateEstimatedCableMeters() {
    let totalPoints = 0;
    this.containers.forEach(container => {
      if (container.section === 'wiring') {
        container.options.forEach(option => {
          if (option.enabled && !option.noCable) {
            totalPoints += option.quantity;
          }
        });
      }
    });
    return Math.ceil(totalPoints * 7);
  }
  
  getCableDiscount() {
    const meters = this.calculateEstimatedCableMeters();
    if (meters > 200) return 20;
    if (meters > 100) return 10;
    if (meters > 50) return 5;
    return 0;
  }
  
  calculateGrandTotal() {
    let total = 0;
    
    this.containers.forEach(container => {
      total += this.calculateContainerTotal(container);
    });
    
    if (this.hasWiringOptions()) {
      const cableMeters = this.calculateEstimatedCableMeters();
      const cablePrice = cableMeters * 100;
      const discount = this.getCableDiscount();
      total += cablePrice * (1 - discount / 100);
    }
    
    return total;
  }
  
  hasAnyEnabledOptions() {
    return this.containers.some(c => c.options.some(o => o.enabled));
  }
  
  hasWiringOptions() {
    return this.containers.some(c => 
      c.section === 'wiring' && c.options.some(o => o.enabled)
    );
  }
  
  clearAll() {
    this.containers = this.getInitialContainers();
    this.render();
    this.updateTotal();
  }
  
  formatPrice(price) {
    return Math.round(price).toLocaleString('ru-RU');
  }
  
  renderOption(container, option) {
    const optionPrice = this.calculateOptionPrice(option);
    const hasDiscount = option.discount && option.quantity >= option.discount.minQty;
    
    return `
      <div class="option-item ${option.enabled ? 'enabled' : ''}">
        <label class="option-label" for="${container.id}-${option.id}">
          <input 
            type="checkbox" 
            id="${container.id}-${option.id}"
            ${option.enabled ? 'checked' : ''}
            onchange="calculator.toggleOption('${container.id}', '${option.id}')"
          />
          <span class="option-name">${option.name}</span>
        </label>
        
        <div class="option-right">
          ${option.enabled ? `
            <div class="quantity-controls">
              <button 
                class="btn-minus" 
                onclick="calculator.updateQuantity('${container.id}', '${option.id}', -1)"
              >−</button>
              <span class="quantity-value">${option.quantity}</span>
              <button 
                class="btn-plus" 
                onclick="calculator.updateQuantity('${container.id}', '${option.id}', 1)"
              >+</button>
            </div>
            <div class="option-price">
              ${this.formatPrice(optionPrice)} ₽
            </div>
          ` : `
            <span class="option-price base">+${this.formatPrice(option.price)} ₽</span>
          `}
        </div>
        
        ${option.enabled && option.discount ? `
          <div class="discount-info ${hasDiscount ? 'active' : ''}">
            💰 Скидка ${option.discount.percent}% от ${option.discount.minQty} шт.
            ${hasDiscount ? ' ✓ Применена!' : ''}
          </div>
        ` : ''}
      </div>
    `;
  }
  
  renderContainer(container) {
    const total = this.calculateContainerTotal(container);
    
    return `
      <div class="service-card">
        <div 
          class="service-header" 
          onclick="calculator.toggleContainer('${container.id}')"
          style="cursor: pointer;"
        >
          <div class="service-icon icon-${container.color}">
            ${container.icon}
          </div>
          <div style="flex: 1;">
            <h3>${container.name}</h3>
            ${container.description ? `<p style="font-size: 12px; color: #6b7280; margin-top: 4px;">${container.description}</p>` : ''}
          </div>
          <span style="font-size: 20px; color: #9ca3af;">${container.expanded ? '▲' : '▼'}</span>
        </div>
        
        ${container.expanded ? `
          <div class="service-options">
            ${container.options.map(opt => this.renderOption(container, opt)).join('')}
          </div>
          
          ${total > 0 ? `
            <div style="margin-top: 16px; padding-top: 16px; border-top: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600; font-size: 14px; color: #374151;">Итого за услугу:</span>
              <span style="font-size: 20px; font-weight: 700; color: #059669;">
                ${this.formatPrice(total)} ₽
              </span>
            </div>
          ` : ''}
        ` : ''}
      </div>
    `;
  }
  
  render() {
    const container = document.getElementById('calculator-container');
    
    let html = '';
    
    const servicesContainers = this.containers.filter(c => c.section === 'services');
    const wiringContainers = this.containers.filter(c => c.section === 'wiring');
    
    // Сервисные контейнеры
    servicesContainers.forEach(c => {
      html += this.renderContainer(c);
    });
    
    // AI-чат вместо контейнера "Электромонтажные работы"
    html += `
      <div class="ai-chat-container">
        <div class="chat-header">
          <div class="chat-header-left">
            <div class="chat-bot-avatar">🤖</div>
            <div class="chat-header-info">
              <h3>AI-консультант</h3>
              <p>Расчёт электромонтажа</p>
            </div>
          </div>
          <button class="chat-reset-btn" onclick="aiChat.reset()">🔄 Начать заново</button>
        </div>
        <div class="chat-body" id="ai-chat-messages"></div>
      </div>
    `;
    
    // Скрытый контейнер для wiring (используется AI-чатом)
    html += '<div style="display: none;">';
    wiringContainers.forEach(c => {
      html += this.renderContainer(c);
    });
    html += '</div>';
    
    container.innerHTML = html;
  }
  
  updateTotal() {
    const hasOptions = this.hasAnyEnabledOptions();
    const hasWiring = this.hasWiringOptions();
    
    const totalSection = document.getElementById('total-section');
    const cableInfoSection = document.getElementById('cable-info-section');
    const orderBtn = document.getElementById('order-btn');
    
    if (hasOptions) {
      totalSection.style.display = 'block';
      orderBtn.style.display = 'block';
      
      const total = this.calculateGrandTotal();
      document.getElementById('calculator-total').textContent = this.formatPrice(total) + ' ₽';
      
      if (hasWiring) {
        const cableMeters = this.calculateEstimatedCableMeters();
        const cableDiscount = this.getCableDiscount();
        
        cableInfoSection.style.display = 'block';
        cableInfoSection.innerHTML = `
          <div class="cable-info">
            <p>💡 Примерный метраж кабеля: <strong>${cableMeters}м</strong></p>
            <p>Автоматически добавлено: <strong>Монтаж кабеля (100₽/м)</strong></p>
            ${cableDiscount > 0 ? `
              <p class="discount-label">✓ Скидка на монтаж кабеля ${cableDiscount}%</p>
            ` : ''}
          </div>
        `;
      } else {
        cableInfoSection.style.display = 'none';
      }
    } else {
      totalSection.style.display = 'none';
      cableInfoSection.style.display = 'none';
      orderBtn.style.display = 'none';
    }
  }
  
  init() {
    this.render();
    this.updateTotal();
  }
  
  getSelectedServices() {
    const selected = [];
    
    this.containers.forEach(container => {
      container.options.forEach(option => {
        if (option.enabled) {
          selected.push({
            container: container.name,
            option: option.name,
            quantity: option.quantity,
            price: this.calculateOptionPrice(option)
          });
        }
      });
    });
    
    if (this.hasWiringOptions()) {
      const cableMeters = this.calculateEstimatedCableMeters();
      const cablePrice = cableMeters * 100;
      const discount = this.getCableDiscount();
      const finalCablePrice = cablePrice * (1 - discount / 100);
      
      selected.push({
        container: 'Автоматически добавлено',
        option: `Монтаж кабеля (примерно ${cableMeters}м)${discount > 0 ? ` — скидка ${discount}%` : ''}`,
        quantity: cableMeters,
        price: finalCablePrice
      });
    }
    
    return selected;
  }
}

function createOrder() {
  const total = calculator.calculateGrandTotal();
  
  if (total === 0) {
    alert('Пожалуйста, выберите хотя бы одну услугу');
    return;
  }
  
  const selected = calculator.getSelectedServices();
  
  let description = 'Заказ из калькулятора:\n\n';
  selected.forEach(item => {
    description += `${item.option} x${item.quantity} = ${calculator.formatPrice(item.price)} ₽\n`;
  });
  description += `\nИТОГО: ${calculator.formatPrice(total)} ₽`;
  
  console.log('Создание заказа:', {
    items: selected,
    total: total,
    description: description
  });
  
  if (confirm(`Итоговая стоимость: ${calculator.formatPrice(total)} ₽\n\nПереход в корзину?`)) {
    window.location.href = '/cart.html';
  }
}

const calculator = new ElectricalCalculator();
