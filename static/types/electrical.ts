export type RoomType = 'room' | '1-room' | '2-room' | '3-room';

export interface RoomDefaults {
  switches: number;
  outlets: number;
}

export const ROOM_DEFAULTS: Record<RoomType, RoomDefaults> = {
  'room': { switches: 1, outlets: 4 },
  '1-room': { switches: 4, outlets: 8 },
  '2-room': { switches: 5, outlets: 10 },
  '3-room': { switches: 7, outlets: 12 }
};

export const ROOM_LABELS: Record<RoomType, string> = {
  'room': 'Комната',
  '1-room': '1-комнатная квартира',
  '2-room': '2-комнатная квартира',
  '3-room': '3-комнатная квартира'
};

export type ProductType = 'switch-single' | 'switch-double' | 'outlet-single' | 'outlet-double' | 'outlet-triple' | 'outlet-quad' | 'outlet-penta' | 'cable' | 'chandelier';

export type ServiceOption = 'install-only' | 'full-wiring' | 'repair';

export interface Product {
  id: string;
  type: ProductType;
  name: string;
  image: string;
  description: string;
  category: 'switch' | 'outlet' | 'cable' | 'chandelier';
  serviceCategory: 'popular' | 'construction';
  installType: 'rough' | 'finish';
  slots: number;
  priceInstallOnly: number;
  priceWithWiring: number;
  discountApplied?: boolean;
  options?: {
    id: string;
    name: string;
    price: number;
  }[];
}

export interface CartItem {
  product: Product;
  quantity: number;
  selectedOption: ServiceOption;
  additionalOptions?: string[];
}

export interface ElectricalItem {
  name: string;
  price: number;
  quantity: number;
  category?: string;
  description?: string;
  isElectricalWork?: boolean;
}

export const ELECTRICAL_WORK_SERVICES = [
  'Блок из 5 розеток',
  'Блок из 4-х розеток',
  'Блок из 3-х розеток',
  'Блок из 2-х розеток',
  'Добавить розетку',
  'Установить розетку',
  'Выключатель перенести',
  'Установить выключатель',
  'Перенос газовых детекторов',
  'Перенос газоанализаторов',
  'монтаж кабеля'
];

export function isElectricalWorkService(serviceName: string): boolean {
  return ELECTRICAL_WORK_SERVICES.some(work => 
    serviceName.toLowerCase().includes(work.toLowerCase())
  );
}

export type OrderStatus = 'pending' | 'confirmed' | 'on-the-way' | 'arrived' | 'in-progress' | 'completed';

export type ExecutorRank = 'specialist' | 'master' | 'senior' | 'expert' | 'legend';

export interface RankInfo {
  id: ExecutorRank;
  name: string;
  description: string;
  responsibilities: string[];
  minCompletedOrders: number;
  minRevenue: number;
  badge: string;
}

export const RANKS: Record<ExecutorRank, RankInfo> = {
  'specialist': {
    id: 'specialist',
    name: 'Специалист',
    description: 'Начальный статус для новых исполнителей',
    responsibilities: [
      'Сверление отверстий',
      'Штробление стен',
      'Установка подрозетников',
      'Прокладка кабеля',
      'Уборка после работ'
    ],
    minCompletedOrders: 0,
    minRevenue: 0,
    badge: '🔧'
  },
  'master': {
    id: 'master',
    name: 'Мастер',
    description: 'Опытный специалист с подтвержденными навыками',
    responsibilities: [
      'Все обязанности Специалиста',
      'Монтаж электрощитов',
      'Подключение автоматов',
      'Диагностика неисправностей'
    ],
    minCompletedOrders: 10,
    minRevenue: 50000,
    badge: '⚡'
  },
  'senior': {
    id: 'senior',
    name: 'Старший мастер',
    description: 'Высококвалифицированный электрик',
    responsibilities: [
      'Все обязанности Мастера',
      'Проектирование электросетей',
      'Сложные монтажные работы',
      'Обучение новичков'
    ],
    minCompletedOrders: 30,
    minRevenue: 150000,
    badge: '⭐'
  },
  'expert': {
    id: 'expert',
    name: 'Эксперт',
    description: 'Профессионал высшего уровня',
    responsibilities: [
      'Все обязанности Старшего мастера',
      'Комплексные электромонтажные системы',
      'Промышленные объекты',
      'Консультирование клиентов'
    ],
    minCompletedOrders: 50,
    minRevenue: 300000,
    badge: '💎'
  },
  'legend': {
    id: 'legend',
    name: 'Легенда',
    description: 'Мастер своего дела с безупречной репутацией',
    responsibilities: [
      'Все виды электромонтажных работ',
      'VIP-клиенты',
      'Особо сложные проекты',
      'Представитель компании'
    ],
    minCompletedOrders: 100,
    minRevenue: 1000000,
    badge: '👑'
  }
};

export type PaymentStatus = 'unpaid' | 'partially_paid' | 'paid' | 'refunded' | 'pending';

export type PaymentMethod = 'cash' | 'card' | 'bank_transfer' | 'yookassa' | 'tinkoff' | 'sberbank';

export interface Payment {
  id: string;
  amount: number;
  method: PaymentMethod;
  status: PaymentStatus;
  createdAt: number;
  confirmedAt?: number;
  externalId?: string;
  receiptUrl?: string;
  description?: string;
}

export interface GoogleCalendarEvent {
  id: string;
  orderId: string;
  eventId: string;
  summary: string;
  description: string;
  startTime: string;
  endTime: string;
  location: string;
  status: 'confirmed' | 'tentative' | 'cancelled';
  createdAt: number;
  updatedAt: number;
}

export interface GoogleKeepNote {
  id: string;
  orderId: string;
  noteId: string;
  title: string;
  content: string;
  createdAt: number;
  updatedAt: number;
}

export interface GoogleIntegrationSettings {
  calendarEnabled: boolean;
  keepEnabled: boolean;
  autoSyncCalendar: boolean;
  autoSyncKeep: boolean;
  accessToken?: string;
  refreshToken?: string;
  tokenExpiry?: number;
}

export interface Order {
  id: string;
  customerName: string;
  customerPhone: string;
  customerEmail?: string;
  date: string;
  time: string;
  address: string;
  phone: string;
  items: ElectricalItem[];
  status: OrderStatus;
  totalSwitches: number;
  totalOutlets: number;
  totalPoints: number;
  estimatedCable: number;
  estimatedFrames: number;
  createdAt: number;
  preferredDate?: string;
  notes?: string;
  assignedTo?: string;
  assignedToName?: string;
  assignedExecutors?: Array<{ id: string; name: string }>;
  totalAmount?: number;
  paymentStatus?: PaymentStatus;
  payments?: Payment[];
  paidAmount?: number;
  googleCalendarEventId?: string;
  googleKeepNoteId?: string;
  googleTaskId?: string;
  departureConfirmedAt?: number;
  arrivedAt?: number;
  isDemo?: boolean;
  viewedBy?: string[];
}

export interface ExecutorEarnings {
  orderId: string;
  totalAmount: number;
  installationWorkAmount: number;
  productAmount: number;
  executorEarnings: number;
  installationEarnings: number;
  productEarnings: number;
}

export function calculateExecutorEarnings(order: Order, executorProfile?: ExecutorProfile): ExecutorEarnings {
  let electricalWorkAmount = 0;
  let otherServicesAmount = 0;

  order.items.forEach(item => {
    const totalItemPrice = item.price * item.quantity;
    
    if (isElectricalWorkService(item.name)) {
      electricalWorkAmount += totalItemPrice;
    } else {
      otherServicesAmount += totalItemPrice;
    }
  });

  const electricalCommission = executorProfile 
    ? getElectricalServicesCommission(executorProfile)
    : 0.3;
  
  const electricalEarnings = electricalWorkAmount * electricalCommission;
  const otherEarnings = otherServicesAmount * 0.5;
  const executorEarnings = electricalEarnings + otherEarnings;

  return {
    orderId: order.id,
    totalAmount: order.totalAmount || 0,
    installationWorkAmount: electricalWorkAmount,
    productAmount: otherServicesAmount,
    executorEarnings: Math.round(executorEarnings),
    installationEarnings: Math.round(electricalEarnings),
    productEarnings: Math.round(otherEarnings)
  };
}

export interface ExecutorProfile {
  userId: string;
  rank: ExecutorRank;
  completedOrders: number;
  totalRevenue: number;
  registrationDate: number;
  lastRankUpdate?: number;
  hasCar?: boolean;
  hasTools?: boolean;
  isActive?: boolean;
  isPro?: boolean;
  hasDiploma?: boolean;
  diplomaVerified?: boolean;
  carVerified?: boolean;
  toolsVerified?: boolean;
  proUnlockedAt?: number;
}

export function calculateRankBonus(profile: ExecutorProfile): number {
  let bonus = 0;
  
  if (profile.hasCar) bonus += 10;
  if (profile.hasTools) bonus += 5;
  if (profile.isActive) bonus += 5;
  
  return bonus;
}

export function checkProStatus(profile: ExecutorProfile): boolean {
  return !!(
    profile.hasDiploma && 
    profile.diplomaVerified &&
    profile.hasCar && 
    profile.carVerified &&
    profile.hasTools && 
    profile.toolsVerified
  );
}

export function getElectricalServicesCommission(profile: ExecutorProfile): number {
  if (profile.isPro) return 0.5;
  
  const registrationDate = profile.registrationDate;
  const threeMonthsAgo = Date.now() - (90 * 24 * 60 * 60 * 1000);
  
  if (registrationDate < threeMonthsAgo) {
    return 0.5;
  }
  
  return 0.3;
}

export function checkRankUpgrade(profile: ExecutorProfile): ExecutorRank | null {
  const currentRank = profile.rank;
  const completedOrders = profile.completedOrders;
  const totalRevenue = profile.totalRevenue;
  
  const ranks: ExecutorRank[] = ['specialist', 'master', 'senior', 'expert', 'legend'];
  const currentIndex = ranks.indexOf(currentRank);
  
  for (let i = ranks.length - 1; i > currentIndex; i--) {
    const rankInfo = RANKS[ranks[i]];
    if (completedOrders >= rankInfo.minCompletedOrders && totalRevenue >= rankInfo.minRevenue) {
      return ranks[i];
    }
  }
  
  return null;
}

export function updateExecutorProfileAfterOrder(
  profile: ExecutorProfile, 
  orderEarnings: ExecutorEarnings
): ExecutorProfile {
  const updatedProfile: ExecutorProfile = {
    ...profile,
    completedOrders: profile.completedOrders + 1,
    totalRevenue: profile.totalRevenue + orderEarnings.executorEarnings
  };
  
  const newRank = checkRankUpgrade(updatedProfile);
  if (newRank && newRank !== profile.rank) {
    updatedProfile.rank = newRank;
    updatedProfile.lastRankUpdate = Date.now();
  }
  
  const shouldBecomePro = checkProStatus(updatedProfile);
  if (shouldBecomePro && !updatedProfile.isPro) {
    updatedProfile.isPro = true;
    updatedProfile.proUnlockedAt = Date.now();
  }
  
  return updatedProfile;
}

export interface PortfolioItem {
  id: string;
  title: string;
  image: string;
  price: string;
  description: string;
}

export const MASTER_VISIT_ID = 'master-visit';

export const PRODUCTS: Product[] = [
  {
    id: MASTER_VISIT_ID,
    type: 'switch-single',
    name: 'Вызов мастера на осмотр',
    image: 'https://cdn.poehali.dev/files/switch-single.jpg',
    description: 'Обязательная услуга при оформлении заявки',
    category: 'switch',
    serviceCategory: 'popular',
    installType: 'finish',
    slots: 0,
    priceInstallOnly: 500,
    priceWithWiring: 500
  },
  {
    id: 'chandelier-1',
    type: 'chandelier',
    name: 'Люстра',
    image: 'https://cdn.poehali.dev/files/chandelier.jpg',
    description: 'Установка люстры',
    category: 'chandelier',
    serviceCategory: 'popular',
    installType: 'finish',
    slots: 0,
    priceInstallOnly: 1000,
    priceWithWiring: 1000,
    options: [
      {
        id: 'dismantle',
        name: 'Демонтаж люстры',
        price: 500
      },
      {
        id: 'assemble',
        name: 'Сборка люстры',
        price: 500
      }
    ]
  },
  {
    id: 'sw-1',
    type: 'switch-single',
    name: 'Установить выключатель',
    image: 'https://cdn.poehali.dev/files/switch-single.jpg',
    description: 'Установка выключателя',
    category: 'switch',
    serviceCategory: 'popular',
    installType: 'finish',
    slots: 1,
    priceInstallOnly: 300,
    priceWithWiring: 1500
  },
  {
    id: 'out-1',
    type: 'outlet-single',
    name: 'Установить розетку',
    image: 'https://cdn.poehali.dev/files/outlet-single.jpg',
    description: 'Черновые работы со штроблением, сверлением и установкой подрозетника',
    category: 'outlet',
    serviceCategory: 'popular',
    installType: 'finish',
    slots: 1,
    priceInstallOnly: 350,
    priceWithWiring: 850,
    options: [
      {
        id: 'block-2',
        name: 'Блок из 2-х розеток',
        price: 1200
      },
      {
        id: 'block-3',
        name: 'Блок из 3-х розеток',
        price: 2500
      },
      {
        id: 'block-4',
        name: 'Блок из 4-х розеток',
        price: 3000
      },
      {
        id: 'block-5',
        name: 'Блок из 5 розеток',
        price: 3500
      }
    ]
  },

];

export function calculateFrames(items: CartItem[]): number {
  let totalFrames = 0;
  
  items.forEach(item => {
    const slots = item.product.slots;
    const quantity = item.quantity;
    
    if (slots === 1 || slots === 2) {
      totalFrames += quantity;
    } else if (slots === 3) {
      totalFrames += quantity;
    } else if (slots === 4) {
      totalFrames += quantity * 2;
    } else if (slots === 5) {
      totalFrames += quantity * 2;
    }
  });
  
  return totalFrames;
}

export function calculateCable(totalFrames: number): number {
  return Math.ceil(totalFrames * 8);
}

export function calculateTotals(items: CartItem[]) {
  let totalSwitches = 0;
  let totalOutlets = 0;
  
  items.forEach(item => {
    const quantity = item.quantity || 0;
    if (item.product.category === 'switch') {
      totalSwitches += quantity;
    } else if (item.product.category === 'outlet') {
      const slots = item.product.slots || 1;
      totalOutlets += quantity * slots;
    }
  });
  
  const totalPoints = totalSwitches + totalOutlets;
  const estimatedFrames = calculateFrames(items) || 0;
  const estimatedCable = calculateCable(estimatedFrames) || 0;
  
  return {
    totalSwitches: totalSwitches || 0,
    totalOutlets: totalOutlets || 0,
    totalPoints: totalPoints || 0,
    estimatedCable: estimatedCable || 0,
    estimatedFrames: estimatedFrames || 0
  };
}

export function calculateItemPrice(item: CartItem): number {
  let basePrice = 0;
  
  const hasInstall = item.additionalOptions?.includes('install') || item.selectedOption === 'install-only';
  const hasWiring = item.additionalOptions?.includes('wiring') || item.selectedOption === 'full-wiring';
  
  if (hasInstall && hasWiring) {
    basePrice = item.product.priceInstallOnly + item.product.priceWithWiring;
  } else if (hasInstall) {
    basePrice = item.product.priceInstallOnly;
  } else if (hasWiring) {
    basePrice = item.product.priceWithWiring;
  } else if (item.selectedOption === 'install-only') {
    basePrice = item.product.priceInstallOnly;
  } else if (item.selectedOption === 'full-wiring') {
    basePrice = item.product.priceWithWiring;
  }
  
  let optionsPrice = 0;
  if (item.additionalOptions && item.product.options) {
    item.additionalOptions.forEach(optionId => {
      if (optionId !== 'install' && optionId !== 'wiring') {
        const option = item.product.options?.find(o => o.id === optionId);
        if (option) {
          optionsPrice += option.price;
        }
      }
    });
  }
  
  const quantity = item.quantity || 1;
  const totalPerItem = basePrice + optionsPrice;
  
  if (item.product.discountApplied) {
    return totalPerItem * quantity;
  }
  
  if (quantity >= 21) {
    return Math.round(totalPerItem * 0.8 * quantity);
  } else if (quantity >= 11) {
    return Math.round(totalPerItem * 0.85 * quantity);
  } else if (quantity >= 6) {
    return Math.round(totalPerItem * 0.9 * quantity);
  } else if (quantity >= 3) {
    return Math.round(totalPerItem * 0.95 * quantity);
  }
  
  return totalPerItem * quantity;
}

export function getDiscount(quantity: number): number {
  if (quantity >= 21) return 20;
  if (quantity >= 11) return 15;
  if (quantity >= 6) return 10;
  if (quantity >= 3) return 5;
  return 0;
}

export function getCableDiscount(cableMeters: number): number {
  if (cableMeters > 200) return 20;
  if (cableMeters > 100) return 10;
  if (cableMeters > 50) return 5;
  return 0;
}