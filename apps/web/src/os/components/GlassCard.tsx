import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { clsx } from '@/lib/clsx'

interface GlassCardProps {
  glow?: boolean
  noPadding?: boolean
  className?: string
  children?: ReactNode
  onClick?: () => void
}

export function GlassCard({ className, glow = false, noPadding = false, children, ...props }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={clsx(
        'relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl',
        'shadow-[0_8px_32px_rgba(0,0,0,0.45)]',
        glow && 'shadow-[0_0_0_1px_rgba(53,200,255,0.25),0_0_40px_rgba(53,200,255,0.12),0_8px_32px_rgba(0,0,0,0.45)]',
        !noPadding && 'p-5',
        className,
      )}
      {...props}
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/[0.04] to-transparent" />
      <div className="relative">{children}</div>
    </motion.div>
  )
}
