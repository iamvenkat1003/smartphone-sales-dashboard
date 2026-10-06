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

import {
  formatCompactCurrency,
  formatCompactNumber,
  formatCurrency,
  formatMonth,
  formatNumber,
} from '../utils/formatters'

const MANUFACTURER_COLORS = ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#f97316', '#8b5cf6']

function ChartTooltip({ active, payload, label, metric, manufacturer = false }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  const value = payload[0].value
  return (
    <div className="chart-tooltip">
      <strong>{manufacturer ? row.manufacturer_name : label}</strong>
      <span>
        {metric === 'revenue' ? formatCurrency(value) : `${formatNumber(value)} units`}
      </span>
      {manufacturer && <small>{row.unit_share_percentage}% unit share</small>}
    </div>
  )
}

export function TopPhonesChart({ data, metric }) {
  const chartData = data.map((phone) => ({
    ...phone,
    displayName: `${phone.manufacturer} ${phone.model_name}`,
  }))

  return (
    <div className="chart chart--bars" aria-label={`Top phones by ${metric}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="#e8edf5" />
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            tickFormatter={metric === 'revenue' ? formatCompactCurrency : formatCompactNumber}
            tick={{ fill: '#718096', fontSize: 11 }}
          />
          <YAxis
            dataKey="displayName"
            type="category"
            width={132}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#334155', fontSize: 12, fontWeight: 600 }}
          />
          <Tooltip
            cursor={{ fill: '#f5f7fb' }}
            content={<ChartTooltip metric={metric} />}
          />
          <Bar
            dataKey={metric === 'revenue' ? 'revenue' : 'units_sold'}
            fill="#4f46e5"
            radius={[0, 6, 6, 0]}
            maxBarSize={24}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ManufacturerChart({ data }) {
  return (
    <div className="manufacturer-chart">
      <div className="donut-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="units_sold"
              nameKey="manufacturer_name"
              innerRadius="64%"
              outerRadius="88%"
              paddingAngle={2}
              stroke="none"
            >
              {data.map((row, index) => (
                <Cell key={row.manufacturer_id} fill={MANUFACTURER_COLORS[index % MANUFACTURER_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip metric="units" manufacturer />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center">
          <strong>{formatNumber(data.reduce((sum, row) => sum + row.units_sold, 0))}</strong>
          <span>Total units</span>
        </div>
      </div>
      <div className="manufacturer-legend">
        {data.map((row, index) => (
          <div className="manufacturer-row" key={row.manufacturer_id}>
            <span
              className="legend-dot"
              style={{ background: MANUFACTURER_COLORS[index % MANUFACTURER_COLORS.length] }}
            />
            <div>
              <strong>{row.manufacturer_name}</strong>
              <small>{formatCompactCurrency(row.revenue)} revenue</small>
            </div>
            <b>{row.unit_share_percentage}%</b>
          </div>
        ))}
      </div>
    </div>
  )
}

export function SalesTrendChart({ data, metric }) {
  const valueKey = metric === 'revenue' ? 'revenue' : 'units_sold'
  return (
    <div className="chart chart--trend" aria-label={`Monthly ${metric} trend`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="salesArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#e8edf5" />
          <XAxis
            dataKey="month"
            tickFormatter={formatMonth}
            interval="preserveStartEnd"
            minTickGap={28}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#718096', fontSize: 11 }}
          />
          <YAxis
            width={64}
            tickFormatter={metric === 'revenue' ? formatCompactCurrency : formatCompactNumber}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#718096', fontSize: 11 }}
          />
          <Tooltip
            labelFormatter={formatMonth}
            formatter={(value) => [
              metric === 'revenue' ? formatCurrency(value) : formatNumber(value),
              metric === 'revenue' ? 'Revenue' : 'Units',
            ]}
            contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 10, boxShadow: '0 8px 24px rgba(15,23,42,.1)' }}
          />
          <Area
            type="monotone"
            dataKey={valueKey}
            stroke="#0284c7"
            strokeWidth={2.5}
            fill="url(#salesArea)"
            activeDot={{ r: 5, strokeWidth: 3, stroke: '#fff' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function PromotionUsageChart({ data }) {
  const chartData = data.map((promotion) => ({
    ...promotion,
    displayName: promotion.promo_name,
  }))

  return (
    <div className="chart chart--promotion" aria-label="Top promotions by usage">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 10, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="#e8edf5" />
          <XAxis
            type="number"
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#718096', fontSize: 11 }}
          />
          <YAxis
            dataKey="displayName"
            type="category"
            width={170}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#334155', fontSize: 11, fontWeight: 600 }}
          />
          <Tooltip
            cursor={{ fill: '#f5f7fb' }}
            formatter={(value) => [formatNumber(value), 'Promotion uses']}
            contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 10, boxShadow: '0 8px 24px rgba(15,23,42,.1)' }}
          />
          <Bar dataKey="times_used" fill="#8b5cf6" radius={[0, 6, 6, 0]} maxBarSize={22} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
