// Калькулятор электромонтажа для Balt-Set.ru
// С динамическими чекбоксами и системой скидок

class ElectricalCalculator {
  constructor() {
    this.services = this.loadServices();
    this.init();
  }
  
  loadServices() {
    return [
      {
        id: 'chandelier',
        name: 'Установить светильник',
        icon: '💡',
        color: 'amber',
        options: [
          { 
            id: 'install', 
            name: 'Установить светильник', 
            price: 1000,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'dismantle', 
            name: 'Демонтаж светильника', 
            price: 500,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'assemble', 
            name: 'Сборка люстры', 
            price: 500,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'crystal', 
            name: 'Подвес хрусталя — 1 час', 
            price: 1500,
            quantity: 0,
            enabled: false
          }
        ]
      },
      {
        id: 'switch',
        name: 'Установить выключатель',
        icon: '🎚️',
        color: 'blue',
        options: [
          { 
            id: 'move', 
            name: 'Добавить выключатель или перенести', 
            price: 1500,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'repair', 
            name: 'Ремонт с учётом материалов', 
            price: 1500,
            quantity: 0,
            enabled: false,
            discount: { minQty: 10, percent: 15 }
          },
          { 
            id: 'replace', 
            name: 'Заменить выключатель', 
            price: 350,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'install', 
            name: 'Установить выключатель', 
            price: 250,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          }
        ]
      },
      {
        id: 'outlet',
        name: 'Установить розетку',
        icon: '🔌',
        color: 'green',
        options: [
          { 
            id: 'repair', 
            name: 'Ремонт с учётом материалов', 
            price: 1500,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'surface', 
            name: 'Накладная розетка', 
            price: 500,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'replace', 
            name: 'Заменить розетку', 
            price: 350,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          },
          { 
            id: 'install', 
            name: 'Установить розетку', 
            price: 250,
            quantity: 0,
            enabled: false,
            discount: { minQty: 5, percent: 10 }
          }
        ]
      },
      {
        id: 'wiring',
        name: 'Электромонтажные работы',
        description: 'Черновые работы со штроблением',
        icon: '⚡',
        color: 'amber',
        options: [
          { 
            id: 'add-outlet', 
            name: 'Добавить розетку', 
            price: 850,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'block-2', 
            name: 'Блок из 2-х розеток', 
            price: 1200,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'move-switch', 
            name: 'Добавить выключатель или перенести', 
            price: 1500,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'block-3', 
            name: 'Блок из 3-х розеток', 
            price: 2500,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'block-4', 
            name: 'Блок из 4-х розеток', 
            price: 3000,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'breaker', 
            name: 'Установка автомата защиты', 
            price: 1000,
            quantity: 0,
            enabled: false,
            discount: { minQty: 10, percent: 50 }  // Большая скидка!
          },
          { 
            id: 'meter', 
            name: 'Установка электросчётчика', 
            price: 3500,
            quantity: 0,
            enabled: false
          },
          { 
            id: 'block-5', 
            name: 'Блок из 5 розеток + закладная', 
            price: 8000,
            quantity: 0,
            enabled: false
          }
        ]
      }
    ];
  }
  
  toggleOption(serviceId, optionId) {
    const service = this.services.find(s => s.id === serviceId);
    const option = service.options.find(o => o.id === optionId);
    
    option.enabled = !option.enabled;
    if (option.enabled && option.quantity === 0) {
      option.quantity = 1;
    }
    
    this.render();
    this.updateTotal();
  }
  
  updateQuantity(serviceId, optionId, delta) {
    const service = this.services.find(s => s.id === serviceId);
    const option = service.options.find(o => o.id === optionId);
    
    const newQuantity = option.quantity + delta;
    if (newQuantity < 1) return;
    
    option.quantity = newQuantity;
    this.render();
    this.updateTotal();
  }
  
  calculateOptionPrice(option) {
    if (!option.enabled) return 0;
    
    let price = option.price * option.quantity;
    
    // ПРИМЕНЕНИЕ СКИДКИ
    if (option.discount && option.quantity >= option.discount.minQty) {
      const discount = option.discount.percent / 100;
      price = price * (1 - discount);
    }
    
    return price;
  }
  
  calculateTotal() {
    let total = 0;
    
    this.services.forEach(service => {
      service.options.forEach(option => {
        total += this.calculateOptionPrice(option);
      });
    });
    
    return total;
  }
  
  hasDiscount(option) {
    return option.discount && option.quantity >= option.discount.minQty;
  }
  
  formatPrice(price) {
    return price.toLocaleString('ru-RU');
  }
  
  render() {
    const container = document.getElementById('calculator-container');
    
    if (this.services.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>Услуги загружаются...</p>
        </div>
      `;
      return;
    }
    
    let html = '';
    
    this.services.forEach(service => {
      html += `
        <div class="service-card">
          <div class="service-header">
            <div class="service-icon icon-${service.color}">
              ${service.icon}
            </div>
            <h3>${service.name}</h3>
          </div>
          <div class="service-options">
      `;
      
      service.options.forEach(option => {
        const optionPrice = this.calculateOptionPrice(option);
        const hasDiscount = this.hasDiscount(option);
        
        html += `
          <div class="option-item ${option.enabled ? 'enabled' : ''}">
            <label class="option-label" for="${service.id}-${option.id}">
              <input 
                type="checkbox" 
                id="${service.id}-${option.id}"
                ${option.enabled ? 'checked' : ''}
                onchange="calculator.toggleOption('${service.id}', '${option.id}')"
              />
              <span class="option-name">${option.name}</span>
            </label>
            
            <div class="option-right">
              ${option.enabled ? `
                <div class="quantity-controls">
                  <button 
                    class="btn-minus" 
                    onclick="calculator.updateQuantity('${service.id}', '${option.id}', -1)"
                    ${option.quantity <= 1 ? 'disabled' : ''}
                  >−</button>
                  <span class="quantity-value">${option.quantity}</span>
                  <button 
                    class="btn-plus" 
                    onclick="calculator.updateQuantity('${service.id}', '${option.id}', 1)"
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
      });
      
      html += `
          </div>
        </div>
      `;
    });
    
    container.innerHTML = html;
  }
  
  updateTotal() {
    const total = this.calculateTotal();
    const totalElement = document.getElementById('calculator-total');
    
    if (totalElement) {
      totalElement.textContent = this.formatPrice(total) + ' ₽';
    }
  }
  
  getSelectedServices() {
    const selected = [];
    
    this.services.forEach(service => {
      service.options.forEach(option => {
        if (option.enabled) {
          selected.push({
            service: service.name,
            option: option.name,
            quantity: option.quantity,
            price: this.calculateOptionPrice(option)
          });
        }
      });
    });
    
    return selected;
  }
  
  init() {
    this.render();
    this.updateTotal();
  }
}

// Создание заказа
function createOrder() {
  const total = calculator.calculateTotal();
  
  if (total === 0) {
    alert('Пожалуйста, выберите хотя бы одну услугу');
    return;
  }
  
  const selected = calculator.getSelectedServices();
  
  // Формирование описания для заказа
  let description = 'Заказ из калькулятора:\n\n';
  selected.forEach(item => {
    description += `${item.option} x${item.quantity} = ${calculator.formatPrice(item.price)} ₽\n`;
  });
  description += `\nИТОГО: ${calculator.formatPrice(total)} ₽`;
  
  // Отправка в Telegram бот или на сервер
  console.log('Создание заказа:', {
    items: selected,
    total: total,
    description: description
  });
  
  // ВАРИАНТ 1: Открыть Telegram бот
  const telegramBotUrl = `https://t.me/YOUR_BOT_USERNAME?start=order_${total}`;
  
  // ВАРИАНТ 2: Отправить на сервер
  // sendToServer(selected, total);
  
  // Для демо - просто показываем alert
  if (confirm(`Итоговая стоимость: ${calculator.formatPrice(total)} ₽\n\nОформить заявку?`)) {
    // Здесь можно перенаправить на страницу оформления или открыть форму
    alert('Спасибо! Мы свяжемся с вами в ближайшее время.\n\n' + description);
  }
}

// Инициализация калькулятора
const calculator = new ElectricalCalculator();
