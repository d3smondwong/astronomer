import React from 'react';
import { cn } from '@/lib/utils';

interface TooltipContextType {
  open?: boolean;
  setOpen?: (open: boolean) => void;
}

const TooltipContext = React.createContext<TooltipContextType>({});

interface TooltipProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children?: React.ReactNode;
}

const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  ({ open, onOpenChange, children }, ref) => {
    const [internalOpen, setInternalOpen] = React.useState(false);
    const isControlled = open !== undefined;
    const currentOpen = isControlled ? open : internalOpen;

    const handleOpenChange = (newOpen: boolean) => {
      if (!isControlled) setInternalOpen(newOpen);
      onOpenChange?.(newOpen);
    };

    return (
      <TooltipContext.Provider value={{ open: currentOpen, setOpen: handleOpenChange }}>
        <div ref={ref}>
          {children}
        </div>
      </TooltipContext.Provider>
    );
  }
);

Tooltip.displayName = 'Tooltip';

interface TooltipTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean;
  children?: React.ReactNode;
}

const TooltipTrigger = React.forwardRef<HTMLDivElement, TooltipTriggerProps>(
  ({ asChild, children, className, ...props }, ref) => {
    const context = React.useContext(TooltipContext);

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ref,
        ...props,
      } as React.ComponentProps<any>);
    }

    return (
      <div
        ref={ref}
        className={cn('cursor-help', className)}
        onMouseEnter={() => context.setOpen?.(true)}
        onMouseLeave={() => context.setOpen?.(false)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

TooltipTrigger.displayName = 'TooltipTrigger';

interface TooltipContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  sideOffset?: number;
}

const TooltipContent = React.forwardRef<HTMLDivElement, TooltipContentProps>(
  ({ children, className, ...props }, ref) => {
    const context = React.useContext(TooltipContext);

    if (!context.open) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'absolute z-50 rounded-md bg-gray-900 px-2 py-1 text-sm text-white shadow-md',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

TooltipContent.displayName = 'TooltipContent';

interface TooltipProviderProps {
  children?: React.ReactNode;
  delayDuration?: number;
}

const TooltipProvider = React.forwardRef<HTMLDivElement, TooltipProviderProps>(
  ({ children }, ref) => {
    return (
      <div ref={ref}>
        {children}
      </div>
    );
  }
);

TooltipProvider.displayName = 'TooltipProvider';

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
