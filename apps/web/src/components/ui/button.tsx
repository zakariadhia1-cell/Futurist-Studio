import type { ButtonHTMLAttributes } from 'react'
import { clsx } from '@/lib/clsx'

type Variant = 'primary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-accent/90 text-bg font-medium hover:bg-accent border border-accent/60',
  ghost:
    'bg-transparent text-text-mid hover:text-text-hi border border-border hover:border-accent/40',
  danger:
    'bg-transparent text-danger border border-danger/40 hover:bg-danger/10',
}

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'rounded-md px-4 py-2 text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}
