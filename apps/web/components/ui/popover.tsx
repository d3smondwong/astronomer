'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface PopoverContextType {
  open?: boolean;
  setOpen?: (open: boolean) => void;
  triggerRef?: React.RefObject<HTMLDivElement | null>;
}

const PopoverContext = React.createContext<PopoverContextType>({});

interface PopoverProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children?: React.ReactNode;
  className?: string;
}

const Popover = React.forwardRef<HTMLDivElement, PopoverProps>(
  ({ open, onOpenChange, children, className }, ref) => {
    const [internalOpen, setInternalOpen] = React.useState(false);
    const isControlled = open !== undefined;
    const currentOpen = isControlled ? open : internalOpen;
    const triggerRef = React.useRef<HTMLDivElement>(null);

    const handleOpenChange = (newOpen: boolean) => {
      if (!isControlled) setInternalOpen(newOpen);
      onOpenChange?.(newOpen);
    };

    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (triggerRef.current && !triggerRef.current.contains(event.target as Node)) {
          const target = event.target as HTMLElement;
          // Check if clicked element is within popover content
          if (!target.closest('[data-popover-content]')) {
            handleOpenChange(false);
          }
        }
      };

      if (currentOpen) {
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
      }
    }, [currentOpen]);

    return (
      <PopoverContext.Provider value={{ open: currentOpen, setOpen: handleOpenChange, triggerRef }}>
        <div ref={ref} className={cn('relative', className)}>
          {children}
        </div>
      </PopoverContext.Provider>
    );
  }
);

Popover.displayName = 'Popover';

interface PopoverTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean;
  children?: React.ReactNode;
}

const PopoverTrigger = React.forwardRef<HTMLDivElement, PopoverTriggerProps>(
  ({ asChild, children, ...props }) => {
    const context = React.useContext(PopoverContext);
    const localRef = React.useRef<HTMLDivElement>(null);

    // Update context triggerRef
    React.useEffect(() => {
      if (context.triggerRef) {
        context.triggerRef.current = localRef.current;
      }
    }, [context.triggerRef]);

    if (asChild && React.isValidElement(children)) {
      const childProps = children.props as any;
      return React.cloneElement(children, {
        ref: localRef,
        onClick: (e: React.MouseEvent) => {
          context.setOpen?.(!context.open);
          childProps.onClick?.(e);
        },
        ...props,
      } as React.ComponentProps<any>);
    }

    return (
      <div
        ref={localRef}
        onClick={() => context.setOpen?.(!context.open)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

PopoverTrigger.displayName = 'PopoverTrigger';

interface PopoverContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  align?: 'start' | 'center' | 'end';
  side?: 'top' | 'right' | 'bottom' | 'left';
  sideOffset?: number;
}

const PopoverContent = React.forwardRef<HTMLDivElement, PopoverContentProps>(
  ({ children, className, align = 'start', side = 'bottom', sideOffset = 4, ...props }, ref) => {
    const context = React.useContext(PopoverContext);

    if (!context.open) return null;

    return (
      <div
        ref={ref}
        data-popover-content="true"
        className={cn(
          'absolute z-50 bg-white text-popover-foreground rounded-md border border-gray-200 shadow-lg',
          side === 'bottom' && 'top-full mt-2',
          side === 'top' && 'bottom-full mb-2',
          side === 'left' && 'right-full mr-2',
          side === 'right' && 'left-full ml-2',
          align === 'start' && 'left-0',
          align === 'center' && 'left-1/2 -translate-x-1/2',
          align === 'end' && 'right-0',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

PopoverContent.displayName = 'PopoverContent';

export { Popover, PopoverTrigger, PopoverContent };
