import { Percent, ShoppingBag, TrendingUp, Users } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { StatTile } from '../components/StatTile'
import { Badge, type BadgeTone } from '../components/Badge'
import { AreaTrend } from '../components/charts'
import { getShopifyStats } from '../data/mock'
import { useMock } from '../data/useMock'
import type { ShopifyOrder } from '../data/types'

const ORDER_STATUS_TONE: Record<ShopifyOrder['status'], BadgeTone> = {
  neu: 'info',
  versendet: 'violet',
  geliefert: 'ok',
  storniert: 'danger',
}

const EUR = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })

export function ShopifyPage() {
  const { data, loading } = useMock(getShopifyStats)

  return (
    <>
      <SectionHeader
        icon={ShoppingBag}
        title="Shopify"
        subtitle="Bestellungen, Umsatz und Shop-Performance - Anbindung an die Shopify Admin API vorbereitet"
      />

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Bestellungen heute" value={String(data.ordersToday)} icon={ShoppingBag} accent="blue" />
            <StatTile label="Umsatz heute" value={EUR.format(data.revenueToday)} icon={TrendingUp} accent="cyan" trend={{ value: '12%', positive: true }} />
            <StatTile label="Umsatz Monat" value={EUR.format(data.revenueMonth)} icon={TrendingUp} accent="violet" />
            <StatTile label="Conversion-Rate" value={`${data.conversionRatePercent}%`} icon={Percent} accent="amber" />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <GlassCard className="lg:col-span-2" glow>
              <div className="mb-2 flex items-center justify-between">
                <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Umsatzverlauf (7 Tage)</div>
                <div className="flex items-center gap-1.5 text-xs text-white/40">
                  <Users className="h-3.5 w-3.5" strokeWidth={1.75} />
                  {data.visitorsToday.toLocaleString('de-DE')} Besucher heute
                </div>
              </div>
              <AreaTrend data={data.revenueTrend} color="var(--color-neon-blue)" />
            </GlassCard>

            <GlassCard>
              <div className="font-mono text-[11px] uppercase tracking-wider text-white/45">Bestseller</div>
              <div className="mt-3 space-y-3">
                {data.bestsellers.map((item, index) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.06] font-mono text-[10px] text-white/50">
                        {index + 1}
                      </span>
                      <div>
                        <div className="text-sm text-white/85">{item.name}</div>
                        <div className="text-xs text-white/35">{item.unitsSold} verkauft</div>
                      </div>
                    </div>
                    <div className="text-sm font-medium text-white">{EUR.format(item.revenue)}</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          <GlassCard className="mt-4" noPadding>
            <div className="p-5 pb-0 font-mono text-[11px] uppercase tracking-wider text-white/45">Letzte Bestellungen</div>
            <div className="mt-3 divide-y divide-white/[0.06]">
              {data.recentOrders.map((order) => (
                <div key={order.id} className="flex items-center justify-between px-5 py-3">
                  <div>
                    <div className="text-sm text-white/85">{order.id}</div>
                    <div className="text-xs text-white/35">{order.customer}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-sm text-white/70">{EUR.format(order.total)}</span>
                    <Badge tone={ORDER_STATUS_TONE[order.status]}>{order.status}</Badge>
                    <span className="hidden text-xs text-white/30 sm:inline">{order.createdAt}</span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </>
      )}
    </>
  )
}
