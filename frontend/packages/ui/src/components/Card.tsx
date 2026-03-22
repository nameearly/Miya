import React from 'react';
import { cn } from '../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'bordered';
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  hover = false,
  children,
  className,
  ...props
}) => {
  const baseStyles = 'rounded-2xl transition-all duration-300';

  const variantStyles = {
    default: 'bg-white shadow-lg',
    glass: 'backdrop-blur-xl bg-white/70 dark:bg-slate-900/70 border border-white/20 shadow-xl',
    bordered: 'bg-white border-2 border-slate-200 shadow-md',
  };

  const hoverStyles = hover
    ? 'hover:shadow-2xl hover:scale-[1.02] hover:-translate-y-1'
    : '';

  return (
    <div
      className={cn(
        baseStyles,
        variantStyles[variant],
        hoverStyles,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={cn('px-6 py-4 border-b border-slate-200', className)} {...props}>
    {children}
  </div>
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={cn('px-6 py-4', className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={cn('px-6 py-4 border-t border-slate-200', className)} {...props}>
    {children}
  </div>
);
