import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const TOOLTIP_STYLE = {
  background: 'rgba(11,15,24,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 10,
  fontSize: 12,
  color: '#e8eaed',
}

export function AreaTrend({
  data,
  dataKey = 'value',
  xKey = 'date',
  color = 'var(--color-neon-blue)',
  height = 180,
}: {
  data: object[]
  dataKey?: string
  xKey?: string
  color?: string
  height?: number
}) {
  const gradientId = `area-${dataKey}-${xKey}`
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.35)" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis stroke="rgba(255,255,255,0.35)" fontSize={11} tickLine={false} axisLine={false} width={36} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: color, strokeOpacity: 0.3 }} />
        <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#${gradientId})`} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function BarComparison({
  data,
  dataKey = 'value',
  xKey = 'label',
  color = 'var(--color-neon-cyan)',
  height = 180,
  layout = 'vertical',
}: {
  data: object[]
  dataKey?: string
  xKey?: string
  color?: string
  height?: number
  layout?: 'vertical' | 'horizontal'
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={layout} margin={{ top: 6, right: 8, bottom: 0, left: layout === 'vertical' ? 8 : 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" horizontal={layout !== 'vertical'} vertical={layout === 'vertical'} />
        {layout === 'vertical' ? (
          <>
            <XAxis type="number" stroke="rgba(255,255,255,0.35)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis dataKey={xKey} type="category" stroke="rgba(255,255,255,0.5)" fontSize={11} tickLine={false} axisLine={false} width={90} />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.35)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(255,255,255,0.35)" fontSize={11} tickLine={false} axisLine={false} width={36} />
          </>
        )}
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
        <Bar dataKey={dataKey} fill={color} radius={4} />
      </BarChart>
    </ResponsiveContainer>
  )
}

const PIE_COLORS = [
  'var(--color-neon-blue)',
  'var(--color-neon-cyan)',
  'var(--color-neon-violet)',
  'var(--color-neon-amber)',
]

export function DonutStat({
  data,
  height = 180,
}: {
  data: { label: string; value: number }[]
  height?: number
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="label" innerRadius="62%" outerRadius="90%" paddingAngle={3} strokeWidth={0}>
          {data.map((entry, index) => (
            <Cell key={entry.label} fill={PIE_COLORS[index % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} />
      </PieChart>
    </ResponsiveContainer>
  )
}
