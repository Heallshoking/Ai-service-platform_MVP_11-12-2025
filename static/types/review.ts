export interface Review {
  id: string;
  orderId: string;
  customerId: string;
  customerName: string;
  electricianId?: string;
  electricianName?: string;
  rating: number;
  comment: string;
  photos: string[];
  createdAt: number;
  response?: {
    text: string;
    createdAt: number;
  };
}

export interface PhotoReport {
  id: string;
  orderId: string;
  uploadedBy: string;
  uploaderRole: 'customer' | 'electrician';
  photos: Array<{
    url: string;
    caption?: string;
    timestamp: number;
  }>;
  createdAt: number;
}

export interface ElectricianRating {
  electricianId: string;
  electricianName: string;
  averageRating: number;
  totalReviews: number;
  completedOrders: number;
  recentReviews: Review[];
}
