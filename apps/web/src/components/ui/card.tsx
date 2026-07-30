import type { HTMLAttributes } from 'react'
import { clsx } from '@/lib/clsx'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx('rounded-xl border border-border bg-panel p-5 shadow-lg shadow-black/20', className)}
      {...props}
    />
  )
}
