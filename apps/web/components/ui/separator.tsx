import React from 'react';
import { cn } from '@/lib/utils';

interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical';
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = 'horizontal' }, ref) => (
    <div
      ref={ref}
      className={cn(
        'bg-gray-200',
        orientation === 'horizontal' ? 'h-px w-full my-4' : 'h-full w-px mx-4',
        className
      )}
    />
  )
);

Separator.displayName = 'Separator';

export { Separator };
