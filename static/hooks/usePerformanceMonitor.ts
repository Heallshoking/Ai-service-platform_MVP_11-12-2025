import { useEffect, useRef } from 'react';

interface PerformanceMetrics {
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
}

export function usePerformanceMonitor(componentName: string, enabled: boolean = false) {
  const metrics = useRef<PerformanceMetrics>({
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
  });
  
  const renderStartTime = useRef<number>(0);

  useEffect(() => {
    if (!enabled) return;
    
    renderStartTime.current = performance.now();
    
    return () => {
      const renderTime = performance.now() - renderStartTime.current;
      metrics.current.renderCount++;
      metrics.current.lastRenderTime = renderTime;
      metrics.current.averageRenderTime = 
        (metrics.current.averageRenderTime * (metrics.current.renderCount - 1) + renderTime) / 
        metrics.current.renderCount;

      if (renderTime > 16) {
        console.warn(
          `[Performance] ${componentName} slow render:`,
          `${renderTime.toFixed(2)}ms`,
          `(avg: ${metrics.current.averageRenderTime.toFixed(2)}ms,`,
          `count: ${metrics.current.renderCount})`
        );
      }
    };
  });

  return metrics.current;
}
