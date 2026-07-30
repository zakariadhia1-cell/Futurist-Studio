import type { InputHTMLAttributes } from 'react'
import { clsx } from '@/lib/clsx'

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        'w-full rounded-md border border-border bg-panel-2 px-3 py-2 text-sm text-text-hi',
        'placeholder:text-text-low outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40',
        className,
      )}
      {...props}
    />
  )
}
