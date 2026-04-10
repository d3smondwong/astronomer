import React from 'react';
import { cn } from '@/lib/utils';

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative w-full overflow-hidden rounded-md border border-gray-200',
        className
      )}
    >
      <div className="overflow-auto">
        {children}
      </div>
    </div>
  )
);

ScrollArea.displayName = 'ScrollArea';

export { ScrollArea };
