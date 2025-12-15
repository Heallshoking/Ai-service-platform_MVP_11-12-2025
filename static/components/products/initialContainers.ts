import { PRODUCTS } from '@/types/electrical';
import { ServiceContainer } from './types';

export function getInitialContainers(): ServiceContainer[] {
  return [
    {
      productId: 'chandelier-1',
      productName: 'Установить светильник',
      productDescription: 'Установка светильника / люстры',
      category: 'chandelier',
      sectionCategory: 'services',
      expanded: false,
      options: [
        { id: 'install', name: 'Установить светильник', price: 1000, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'dismantle', name: 'Демонтаж светильника', price: 500, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'assemble', name: 'Сборка люстры', price: 500, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'crystal', name: 'Подвес хрусталя — 1 час', price: 1500, quantity: 1, enabled: false },
      ]
    },
    {
      productId: 'sw-install',
      productName: 'Установить выключатель',
      productDescription: 'Установка выключателя, ремонт',
      category: 'switch',
      sectionCategory: 'services',
      expanded: false,
      options: [
        { id: 'move-switch-alt', name: 'Добавить выключатель или перенести розетку в другое место', price: 1500, quantity: 1, enabled: false },
        { id: 'repair', name: 'Ремонт с учётом материалов', price: 1500, quantity: 1, enabled: false, discount: { minQuantity: 10, percent: 15 } },
        { id: 'replace-switch', name: 'Заменить выключатель', price: 350, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'install', name: 'Установить выключатель', price: 250, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
      ]
    },
    {
      productId: 'out-install',
      productName: 'Установить розетку',
      productDescription: 'Установка розеток, ремонт',
      category: 'outlet',
      sectionCategory: 'services',
      expanded: false,
      options: [
        { id: 'repair', name: 'Ремонт с учётом материалов', price: 1500, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'surface-outlet', name: 'Накладная розетка', price: 500, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'replace-outlet', name: 'Заменить розетку', price: 350, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
        { id: 'install', name: 'Установить розетку', price: 250, quantity: 1, enabled: false, discount: { minQuantity: 5, percent: 10 } },
      ]
    },
    {
      productId: 'wiring-complex',
      productName: 'Электромонтажные работы',
      productDescription: 'Черновые работы со штроблением, сверлением и установкой подрозетника, комплексная замена проводки в Калининграде.',
      videoUrl: 'https://vk.com/clip1166188_456239923',
      category: 'outlet',
      sectionCategory: 'wiring',
      expanded: true,
      options: [
        { id: 'add-outlet', name: 'Добавить розетку', price: 850, quantity: 1, enabled: false },
        { id: 'breaker-install', name: 'Установка автомата защиты', price: 1000, quantity: 1, enabled: false, discount: { minQuantity: 10, percent: 50 }, group: 'panel', noCable: true },
        { id: 'block-2', name: 'Блок из 2-х розеток', price: 1200, quantity: 1, enabled: false },
        { id: 'move-switch', name: 'Добавить выключатель или перенести розетку в другое место', price: 1500, quantity: 1, enabled: false },
        { id: 'block-3', name: 'Блок из 3-х розеток', price: 2500, quantity: 1, enabled: false },
        { id: 'box-surface', name: 'Бокс открытого монтажа', price: 2500, quantity: 1, enabled: false, group: 'panel', noCable: true },
        { id: 'input-cable', name: 'Новый вводной кабель', price: 2500, quantity: 1, enabled: false, group: 'panel' },
        { id: 'block-4', name: 'Блок из 4-х розеток', price: 3000, quantity: 1, enabled: false },
        { id: 'breaker-replace', name: 'Замена автомата с учётом материала', price: 3000, quantity: 1, enabled: false, group: 'panel', noCable: true },
        { id: 'gas-sensor', name: 'Перенос газовых детекторов', price: 3500, quantity: 1, enabled: false },
        { id: 'meter', name: 'Установка электросчётчика', price: 3500, quantity: 1, enabled: false, group: 'panel', voltageOptions: { '220V': 3500, '380V': 5500 }, selectedVoltage: '220V', noCable: true },
        { id: 'box-flush', name: 'Бокс скрытого монтажа', price: 8000, quantity: 1, enabled: false, group: 'panel', noCable: true },
        { id: 'block-5', name: 'Блок из 5 розеток +закладная', price: 8000, quantity: 1, enabled: false },
        { id: 'equipment-fee', name: 'Обязательные расходы на спецоборудование и расходные материалы (алмазные диски, мешки для пылесоса, газ и т.д.)', price: 2500, quantity: 1, enabled: false, isInfo: true },
      ]
    }
  ];
}