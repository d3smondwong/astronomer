import React, { createContext, useContext } from 'react';
import { cn } from '@/lib/utils';

interface RadioGroupContextType {
  value?: string | number;
  onValueChange?: (value: string | number) => void;
}

const RadioGroupContext = createContext<RadioGroupContextType>({});

interface RadioGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string | number;
  onValueChange?: (value: string | number) => void;
  disabled?: boolean;
}

const RadioGroup = React.forwardRef<HTMLDivElement, RadioGroupProps>(
  ({ className, value, onValueChange, disabled, ...props }, ref) => {
    return (
      <RadioGroupContext.Provider value={{ value, onValueChange }}>
        <div
          ref={ref}
          className={cn('flex flex-col space-y-2', className)}
          {...props}
        />
      </RadioGroupContext.Provider>
    );
  }
);

RadioGroup.displayName = 'RadioGroup';

interface RadioGroupItemProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value?: string | number;
  id?: string;
}

const RadioGroupItem = React.forwardRef<HTMLInputElement, RadioGroupItemProps>(
  ({ className, value, id, ...props }, ref) => {
    const context = useContext(RadioGroupContext);

    return (
      <input
        ref={ref}
        type="radio"
        value={value}
        id={id}
        checked={context.value === value}
        onChange={(e) => {
          context.onValueChange?.(e.target.value as string | number);
        }}
        className={cn(
          'h-4 w-4 border border-gray-300 bg-white checked:bg-blue-600 checked:border-blue-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-0 disabled:opacity-50 disabled:cursor-not-allowed',
          className
        )}
        {...props}
      />
    );
  }
);

RadioGroupItem.displayName = 'RadioGroupItem';

export { RadioGroup, RadioGroupItem };
