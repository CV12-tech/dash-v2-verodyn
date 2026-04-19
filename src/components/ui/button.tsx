import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

/**
 * Verodyn spec: "Hover-State verändert die Hintergrundhelligkeit minimal,
 * statt die Farbe komplett zu wechseln." — tiny brightness shift, never a hue swap.
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-[filter,background-color,border-color] duration-150 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary:   'bg-primary text-primary-fg hover:brightness-[1.08] active:brightness-95',
        secondary: 'bg-surface-muted text-ink hover:bg-surface-sunken',
        outline:   'border border-border-strong bg-transparent text-ink hover:bg-surface-muted',
        ghost:     'bg-transparent text-ink-muted hover:bg-surface-muted hover:text-ink',
        danger:    'bg-warning text-white hover:brightness-[1.08]',
      },
      size: {
        sm:   'h-8 px-3 text-xs',
        md:   'h-10 px-4 text-sm',
        lg:   'h-12 px-6 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = 'button', ...props }, ref) => (
    <button ref={ref} type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  ),
);
Button.displayName = 'Button';
