import React from 'react';
import { Modal } from 'antd';
import { cn } from '@/lib/utils';

interface AlertDialogContextType {
  open?: boolean;
  setOpen?: (open: boolean) => void;
}

const AlertDialogContext = React.createContext<AlertDialogContextType>({});

interface AlertDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children?: React.ReactNode;
}

const AlertDialog = React.forwardRef<HTMLDivElement, AlertDialogProps>(
  ({ open, onOpenChange, children }, ref) => {
    const [internalOpen, setInternalOpen] = React.useState(false);
    const isControlled = open !== undefined;
    const currentOpen = isControlled ? open : internalOpen;

    const handleOpenChange = (newOpen: boolean) => {
      if (!isControlled) setInternalOpen(newOpen);
      onOpenChange?.(newOpen);
    };

    return (
      <AlertDialogContext.Provider value={{ open: currentOpen, setOpen: handleOpenChange }}>
        <div ref={ref}>
          {children}
        </div>
      </AlertDialogContext.Provider>
    );
  }
);

AlertDialog.displayName = 'AlertDialog';

interface AlertDialogTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  children?: React.ReactNode;
}

const AlertDialogTrigger = React.forwardRef<HTMLButtonElement, AlertDialogTriggerProps>(
  ({ asChild, children, className, ...props }, ref) => {
    const context = React.useContext(AlertDialogContext);

    if (asChild && React.isValidElement(children)) {
      const childProps = children.props as any;
      return React.cloneElement(children, {
        ref,
        onClick: (e: React.MouseEvent) => {
          context.setOpen?.(true);
          childProps.onClick?.(e);
        },
        ...props,
      } as React.ComponentProps<any>);
    }

    return (
      <button
        ref={ref}
        onClick={() => context.setOpen?.(true)}
        className={cn('', className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

AlertDialogTrigger.displayName = 'AlertDialogTrigger';

interface AlertDialogContentProps {
  children?: React.ReactNode;
  className?: string;
}

const AlertDialogContent = React.forwardRef<HTMLDivElement, AlertDialogContentProps>(
  ({ children, className }) => {
    const context = React.useContext(AlertDialogContext);

    return (
      <Modal
        open={context.open}
        onCancel={() => context.setOpen?.(false)}
        footer={null}
        className={cn('', className)}
      >
        {children}
      </Modal>
    );
  }
);

AlertDialogContent.displayName = 'AlertDialogContent';

interface AlertDialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const AlertDialogHeader = React.forwardRef<HTMLDivElement, AlertDialogHeaderProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-2 text-left sm:text-left', className)}
      {...props}
    >
      {children}
    </div>
  )
);

AlertDialogHeader.displayName = 'AlertDialogHeader';

interface AlertDialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const AlertDialogFooter = React.forwardRef<HTMLDivElement, AlertDialogFooterProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-6', className)}
      {...props}
    >
      {children}
    </div>
  )
);

AlertDialogFooter.displayName = 'AlertDialogFooter';

interface AlertDialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children?: React.ReactNode;
}

const AlertDialogTitle = React.forwardRef<HTMLHeadingElement, AlertDialogTitleProps>(
  ({ className, children, ...props }, ref) => (
    <h2
      ref={ref}
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    >
      {children}
    </h2>
  )
);

AlertDialogTitle.displayName = 'AlertDialogTitle';

interface AlertDialogDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children?: React.ReactNode;
}

const AlertDialogDescription = React.forwardRef<HTMLParagraphElement, AlertDialogDescriptionProps>(
  ({ className, children, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-gray-500', className)}
      {...props}
    >
      {children}
    </p>
  )
);

AlertDialogDescription.displayName = 'AlertDialogDescription';

interface AlertDialogActionProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode;
}

const AlertDialogAction = React.forwardRef<HTMLButtonElement, AlertDialogActionProps>(
  ({ onClick, className, children, ...props }, ref) => {
    const context = React.useContext(AlertDialogContext);

    return (
      <button
        ref={ref}
        onClick={(e) => {
          onClick?.(e);
          context.setOpen?.(false);
        }}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10 px-4 py-2 bg-red-600 text-white hover:bg-red-700',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

AlertDialogAction.displayName = 'AlertDialogAction';

interface AlertDialogCancelProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode;
}

const AlertDialogCancel = React.forwardRef<HTMLButtonElement, AlertDialogCancelProps>(
  ({ onClick, className, children, ...props }, ref) => {
    const context = React.useContext(AlertDialogContext);

    return (
      <button
        ref={ref}
        onClick={(e) => {
          onClick?.(e);
          context.setOpen?.(false);
        }}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10 px-4 py-2 border border-gray-300 bg-white text-gray-900 hover:bg-gray-50',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

AlertDialogCancel.displayName = 'AlertDialogCancel';

export {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
};
