import React from 'react';
import { Avatar as AntAvatar, AvatarProps as AntAvatarProps } from 'antd';
import { cn } from '@/lib/utils';

interface AvatarProps extends AntAvatarProps {
  children?: React.ReactNode;
}

const Avatar = React.forwardRef<HTMLSpanElement, AvatarProps>(
  ({ className, size = 40, ...props }, ref) => (
    <AntAvatar
      ref={ref}
      size={size}
      className={cn('rounded-full', className)}
      {...props}
    />
  )
);

Avatar.displayName = 'Avatar';

interface AvatarImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {}

const AvatarImage = React.forwardRef<HTMLImageElement, AvatarImageProps>(
  ({ className, src, alt, ...props }, ref) => (
    <img
      ref={ref}
      src={src}
      alt={alt}
      className={cn('rounded-full object-cover', className)}
      {...props}
    />
  )
);

AvatarImage.displayName = 'AvatarImage';

interface AvatarFallbackProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

const AvatarFallback = React.forwardRef<HTMLDivElement, AvatarFallbackProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex items-center justify-center h-10 w-10 rounded-full bg-gray-200 text-gray-700 text-sm font-medium',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);

AvatarFallback.displayName = 'AvatarFallback';

export { Avatar, AvatarImage, AvatarFallback };
