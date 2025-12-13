export interface Service {
  id: string;
  title: string;
  description: string;
  price: number;
  icon: string;
  quantity?: number;
}

export interface Executor {
  id: number;
  name: string;
  phone: string;
  rating: number;
  experience_years: number;
}

export const services: Service[] = [
  { id: '1', title: 'Установка розеток', description: 'Установка и замена розеток любого типа', price: 500, icon: 'Plug', quantity: 0 },
  { id: '2', title: 'Установка выключателей', description: 'Монтаж одно- и многоклавишных выключателей', price: 400, icon: 'ToggleLeft', quantity: 0 },
  { id: '3', title: 'Монтаж освещения', description: 'Установка люстр, светильников, LED-подсветки', price: 800, icon: 'Lightbulb', quantity: 0 },
  { id: '4', title: 'Сборка щитков', description: 'Монтаж и настройка электрических щитов', price: 3000, icon: 'Box', quantity: 0 },
  { id: '5', title: 'Проводка квартиры', description: 'Полная замена электропроводки в квартире', price: 1200, icon: 'Cable', quantity: 0 },
  { id: '6', title: 'Диагностика', description: 'Поиск неисправностей и консультация', price: 1000, icon: 'Search', quantity: 0 }
];
