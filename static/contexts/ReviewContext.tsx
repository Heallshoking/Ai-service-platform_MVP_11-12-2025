import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Review, PhotoReport, ElectricianRating } from '@/types/review';

interface ReviewContextType {
  reviews: Review[];
  photoReports: PhotoReport[];
  addReview: (review: Omit<Review, 'id' | 'createdAt'>) => void;
  addPhotoReport: (report: Omit<PhotoReport, 'id' | 'createdAt'>) => void;
  getOrderReviews: (orderId: string) => Review[];
  getOrderPhotoReports: (orderId: string) => PhotoReport[];
  getElectricianRating: (electricianId: string) => ElectricianRating | null;
  addReviewResponse: (reviewId: string, response: string) => void;
}

const ReviewContext = createContext<ReviewContextType | undefined>(undefined);

export function ReviewProvider({ children }: { children: ReactNode }) {
  const [reviews, setReviews] = useState<Review[]>(() => {
    const saved = localStorage.getItem('reviews');
    return saved ? JSON.parse(saved) : [];
  });

  const [photoReports, setPhotoReports] = useState<PhotoReport[]>(() => {
    const saved = localStorage.getItem('photoReports');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('reviews', JSON.stringify(reviews));
  }, [reviews]);

  useEffect(() => {
    localStorage.setItem('photoReports', JSON.stringify(photoReports));
  }, [photoReports]);

  const addReview = (reviewData: Omit<Review, 'id' | 'createdAt'>) => {
    const newReview: Review = {
      ...reviewData,
      id: `review-${Date.now()}-${Math.random()}`,
      createdAt: Date.now()
    };

    setReviews(prev => [newReview, ...prev]);
  };

  const addPhotoReport = (reportData: Omit<PhotoReport, 'id' | 'createdAt'>) => {
    const newReport: PhotoReport = {
      ...reportData,
      id: `report-${Date.now()}-${Math.random()}`,
      createdAt: Date.now()
    };

    setPhotoReports(prev => [newReport, ...prev]);
  };

  const getOrderReviews = (orderId: string) => {
    return reviews.filter(review => review.orderId === orderId);
  };

  const getOrderPhotoReports = (orderId: string) => {
    return photoReports.filter(report => report.orderId === orderId);
  };

  const getElectricianRating = (electricianId: string): ElectricianRating | null => {
    const electricianReviews = reviews.filter(r => r.electricianId === electricianId);
    
    if (electricianReviews.length === 0) return null;

    const totalRating = electricianReviews.reduce((sum, r) => sum + r.rating, 0);
    const averageRating = totalRating / electricianReviews.length;

    return {
      electricianId,
      electricianName: electricianReviews[0]?.electricianName || 'Мастер',
      averageRating: Math.round(averageRating * 10) / 10,
      totalReviews: electricianReviews.length,
      completedOrders: electricianReviews.length,
      recentReviews: electricianReviews.slice(0, 5)
    };
  };

  const addReviewResponse = (reviewId: string, responseText: string) => {
    setReviews(prev =>
      prev.map(review =>
        review.id === reviewId
          ? {
              ...review,
              response: {
                text: responseText,
                createdAt: Date.now()
              }
            }
          : review
      )
    );
  };

  return (
    <ReviewContext.Provider
      value={{
        reviews,
        photoReports,
        addReview,
        addPhotoReport,
        getOrderReviews,
        getOrderPhotoReports,
        getElectricianRating,
        addReviewResponse
      }}
    >
      {children}
    </ReviewContext.Provider>
  );
}

export function useReviews() {
  const context = useContext(ReviewContext);
  if (!context) {
    throw new Error('useReviews must be used within ReviewProvider');
  }
  return context;
}
