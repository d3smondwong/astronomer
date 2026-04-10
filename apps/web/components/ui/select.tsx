import React from 'react';
import { Select as AntSelect, SelectProps as AntSelectProps } from 'antd';
import { cn } from '@/lib/utils';

interface SelectContextType {
  value?: string;
  onValueChange?: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextType>({});

interface SelectProps extends Omit<AntSelectProps<any>, 'value' | 'onChange'> {
  value?: string;
  onValueChange?: (value: string) => void;
  children?: React.ReactNode;
}

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({ value, onValueChange, children, ...props }, ref) => {
    const handleChange = (val: string) => {
      onValueChange?.(val);
    };

    return (
      <SelectContext.Provider value={{ value, onValueChange }}>
        <div ref={ref}>
          <AntSelect
            value={value}
            onChange={handleChange}
            {...(props as any)}
          >
            {children}
          </AntSelect>
        </div>
      </SelectContext.Provider>
    );
  }
);

Select.displayName = 'Select';

interface SelectTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const SelectTrigger = React.forwardRef<HTMLDivElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);

SelectTrigger.displayName = 'SelectTrigger';

interface SelectValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  placeholder?: string;
  children?: React.ReactNode;
}

const SelectValue = React.forwardRef<HTMLSpanElement, SelectValueProps>(
  ({ placeholder, className, children, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <span
        ref={ref}
        className={cn('text-gray-600', !context.value && 'text-gray-400', className)}
        {...props}
      >
        {children || placeholder}
      </span>
    );
  }
);

SelectValue.displayName = 'SelectValue';

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white p-1 text-gray-950 shadow-md',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);

SelectContent.displayName = 'SelectContent';

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
  disabled?: boolean;
  children?: React.ReactNode;
}

const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
  ({ value, disabled, className, children, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100',
          context.value === value && 'bg-blue-100',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

SelectItem.displayName = 'SelectItem';

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
