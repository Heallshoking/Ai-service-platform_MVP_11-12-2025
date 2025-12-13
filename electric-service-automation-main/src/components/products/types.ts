export interface ServiceOption {
  id: string;
  name: string;
  price: number;
  quantity: number;
  enabled: boolean;
  description?: string;
  unit?: string;
  group?: 'construction' | 'panel';
  discount?: {
    minQuantity: number;
    percent: number;
  };
  customPrice?: boolean;
  voltageOptions?: {
    '220V': number;
    '380V': number;
  };
  selectedVoltage?: '220V' | '380V';
  noCable?: boolean;
  isInfo?: boolean;
}

export interface ServiceContainer {
  productId: string;
  productName: string;
  productDescription: string;
  videoUrl?: string;
  category: string;
  sectionCategory: 'services' | 'wiring';
  options: ServiceOption[];
  expanded: boolean;
}