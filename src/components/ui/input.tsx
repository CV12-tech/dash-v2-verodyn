import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: ReactNode;
  error?: string | undefined;
  hint?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const generated = useId();
    const inputId = id ?? generated;
    const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-sm font-medium text-ink">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy}
          className={cn(
            'h-10 rounded-lg border border-border bg-surface px-3 text-sm text-ink placeholder:text-ink-subtle',
            'transition-colors focus:border-primary focus:outline-none',
            error && 'border-warning focus:border-warning',
            className,
          )}
          {...props}
        />
        {error ? (
          <p id={`${inputId}-error`} className="text-xs text-warning">{error}</p>
        ) : hint ? (
          <p id={`${inputId}-hint`} className="text-xs text-ink-muted">{hint}</p>
        ) : null}
      </div>
    );
  },
);
Input.displayName = 'Input';
