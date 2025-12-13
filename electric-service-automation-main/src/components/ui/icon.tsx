import React from 'react';
import * as LucideIcons from 'lucide-react';
import { LucideProps } from 'lucide-react';

interface IconProps extends LucideProps {
  name: string;
  fallback?: string;
}

const Icon = React.forwardRef<SVGSVGElement, IconProps>(
  ({ name, fallback = 'CircleAlert', ...props }, ref) => {
    const IconComponent = (LucideIcons as Record<string, React.FC<LucideProps>>)[name];

    if (!IconComponent) {
      const FallbackIcon = (LucideIcons as Record<string, React.FC<LucideProps>>)[fallback];

      if (!FallbackIcon) {
        return <span className="text-xs text-gray-400">[icon]</span>;
      }

      return <FallbackIcon ref={ref} {...props} />;
    }

    return <IconComponent ref={ref} {...props} />;
  }
);

Icon.displayName = 'Icon';

export default Icon;
