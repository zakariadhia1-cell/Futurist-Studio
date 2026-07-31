import { motion } from 'framer-motion'
import { clsx } from '@/lib/clsx'

export function ProgressBar({
  percent,
  tone = 'blue',
  className,
  height = 'h-1.5',
}: {
  percent: number
  tone?: 'blue' | 'cyan' | 'violet' | 'amber' | 'red' | 'ok'
  className?: string
  height?: string
}) {
  const clamped = Math.max(0, Math.min(100, percent))
  const colorVar =
    tone === 'ok'
      ? 'var(--color-ok)'
      : tone === 'amber'
        ? 'var(--color-neon-amber)'
        : tone === 'red'
          ? 'var(--color-neon-red)'
          : tone === 'violet'
            ? 'var(--color-neon-violet)'
            : tone === 'cyan'
              ? 'var(--color-neon-cyan)'
              : 'var(--color-neon-blue)'

  return (
    <div className={clsx('w-full overflow-hidden rounded-full bg-white/[0.06]', height, className)}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${clamped}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="h-full rounded-full"
        style={{ background: colorVar, boxShadow: `0 0 8px ${colorVar}` }}
      />
    </div>
  )
}
