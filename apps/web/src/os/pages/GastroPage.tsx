import { Clock, Star, TrendingUp, UtensilsCrossed } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { StatTile } from '../components/StatTile'
import { Badge, type BadgeTone } from '../components/Badge'
import { getGastroStats } from '../data/mock'
import { useMock } from '../data/useMock'
import type { GastroOrder } from '../data/types'

const DELIVERY_LABEL: Record<GastroOrder['deliveryStatus'], string> = {
  in_kueche: 'In der Kueche',
  unterwegs: 'Unterwegs',
  geliefert: 'Geliefert',
  storniert: 'Storniert',
}

const DELIVERY_TONE: Record<GastroOrder['deliveryStatus'], BadgeTone> = {
  in_kueche: 'warn',
  unterwegs: 'info',
  geliefert: 'ok',
  storniert: 'danger',
}

const EUR = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })

export function GastroPage() {
  const { data, loading } = useMock(getGastroStats)

  return (
    <>
      <SectionHeader
        icon={UtensilsCrossed}
        title="Gastro Prinz"
        subtitle="Bestellungen, Lieferstatus, Bewertungen und Social Media - noch ohne echte Anbindung, Datenform bereits API-kompatibel"
      />

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Bestellungen heute" value={String(data.ordersToday)} icon={UtensilsCrossed} accent="blue" />
            <StatTile label="Umsatz heute" value={EUR.format(data.revenueToday)} icon={TrendingUp} accent="cyan" trend={{ value: '8%', positive: true }} />
            <StatTile label="Oe Lieferzeit" value={`${data.avgDeliveryMinutes} Min.`} icon={Clock} accent="amber" />
            <StatTile label="Google-Bewertung" value={`${data.googleRating.toFixed(1)} / 5`} icon={Star} accent="violet" trend={{ value: `${data.googleReviewCount} Bewertungen`, positive: true }} />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <GlassCard className="lg:col-span-2" noPadding glow>
              <div className="p-5 pb-0 font-mono text-[11px] uppercase tracking-wider text-white/45">Laufende Bestellungen</div>
              <div className="mt-3 divide-y divide-white/[0.06]">
                {data.recentOrders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between px-5 py-3">
                    <div>
                      <div className="text-sm text-white/85">
                        {order.id} <span className="text-white/35">- {order.customer}</span>
                      </div>
                      <div className="text-xs text-white/35">{order.items} Artikel</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-mono text-sm text-white/70">{EUR.format(order.total)}</span>
                      <Badge tone={DELIVERY_TONE[order.deliveryStatus]}>{DELIVERY_LABEL[order.deliveryStatus]}</Badge>
                      <span className="hidden text-xs text-white/30 sm:inline">{order.createdAt}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-5" />
            </GlassCard>

            <GlassCard>
              <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Social Media</div>
              <div className="mt-3 space-y-4">
                {data.socialStats.map((stat) => (
                  <div key={stat.platform} className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-white/85">{stat.platform}</div>
                      <div className="text-xs text-white/35">{stat.followers.toLocaleString('de-DE')} Follower</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white/70">{stat.engagementPercent}% Engagement</div>
                      <div className={`text-xs ${stat.changePercent >= 0 ? 'text-[color:var(--color-ok)]' : 'text-[color:var(--color-neon-red)]'}`}>
                        {stat.changePercent >= 0 ? '+' : ''}
                        {stat.changePercent}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </>
      )}
    </>
  )
}
