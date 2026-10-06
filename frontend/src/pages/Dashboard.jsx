import { useState } from 'react'

import { ManufacturerChart, SalesTrendChart, TopPhonesChart } from '../components/AnalyticsCharts'
import CustomerInsights from '../components/CustomerInsights'
import KpiCard from '../components/KpiCard'
import PhoneArtwork from '../components/PhoneArtwork'
import SectionCard from '../components/SectionCard'
import SegmentedControl from '../components/SegmentedControl'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useApi } from '../hooks/useApi'
import {
  getCustomerInsights,
  getKPIs,
  getManufacturers,
  getPromotions,
  getSalesTrend,
  getTopPhones,
} from '../services/api'
import {
  formatCompactCurrency,
  formatCurrency,
  formatNumber,
} from '../utils/formatters'

const metricOptions = [
  { label: 'Units', value: 'units' },
  { label: 'Revenue', value: 'revenue' },
]

function KpiSection() {
  const { data, error, loading, reload } = useApi(getKPIs, [])

  if (loading) return <LoadingState label="Loading performance summary…" compact />
  if (error) return <ErrorState error={error} onRetry={reload} compact />

  return (
    <div className="kpi-grid">
      <KpiCard
        label="Total Revenue"
        value={formatCompactCurrency(data.total_revenue)}
        detail={`${formatNumber(data.total_transactions)} sales transactions`}
        tone="indigo"
      />
      <KpiCard
        label="Units Sold"
        value={formatNumber(data.total_units_sold)}
        detail="Across all phone configurations"
        tone="sky"
      />
      <KpiCard
        label="Customers"
        value={formatNumber(data.total_customers)}
        detail="Unique purchasing customers"
        tone="emerald"
      />
      <KpiCard
        label="Average Selling Price"
        value={formatCurrency(data.average_selling_price)}
        detail="Quantity-weighted price per unit"
        tone="amber"
      />
    </div>
  )
}

function TopPhonesSection() {
  const [metric, setMetric] = useState('units')
  const { data, error, loading, reload } = useApi(
    () => getTopPhones(metric, 5),
    [metric],
  )

  return (
    <SectionCard
      title="Top Selling Phones"
      description={`Ranked by ${metric === 'units' ? 'units sold' : 'sales revenue'}`}
      action={(
        <SegmentedControl
          value={metric}
          options={metricOptions}
          onChange={setMetric}
          label="Top phone ranking metric"
        />
      )}
    >
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !data?.length ? <EmptyState /> : <TopPhonesChart data={data} metric={metric} />}
    </SectionCard>
  )
}

function TopPhoneFeature({ onCompare }) {
  const { data, error, loading, reload } = useApi(() => getTopPhones('units', 1), [])
  const phone = data?.[0]

  return (
    <SectionCard
      title="Market Leader"
      description="Current top seller by unit volume"
      className="feature-section"
    >
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !phone ? <EmptyState /> : (
        <div className="phone-feature">
          <div className="phone-feature__visual">
            <span className="rank-badge">#1</span>
            <PhoneArtwork imagePath={phone.image_path} modelName={phone.model_name} size="large" />
          </div>
          <div className="phone-feature__content">
            <p>{phone.manufacturer}</p>
            <h3>{phone.model_name}</h3>
            <div className="feature-stats">
              <div><span>Units sold</span><strong>{formatNumber(phone.units_sold)}</strong></div>
              <div><span>Revenue</span><strong>{formatCompactCurrency(phone.revenue)}</strong></div>
              <div><span>Avg. price</span><strong>{formatCurrency(phone.average_selling_price)}</strong></div>
            </div>
            <button className="button button--primary" type="button" onClick={onCompare}>
              Compare phones <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      )}
    </SectionCard>
  )
}

function ManufacturerSection() {
  const { data, error, loading, reload } = useApi(getManufacturers, [])
  return (
    <SectionCard title="Manufacturer Performance" description="Unit market share and revenue contribution">
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !data?.length ? <EmptyState /> : <ManufacturerChart data={data} />}
    </SectionCard>
  )
}

function TrendSection() {
  const [metric, setMetric] = useState('revenue')
  const { data, error, loading, reload } = useApi(getSalesTrend, [])
  return (
    <SectionCard
      title="Sales Trend"
      description="Monthly performance and seasonal demand"
      action={<SegmentedControl value={metric} options={metricOptions} onChange={setMetric} label="Sales trend metric" />}
    >
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !data?.length ? <EmptyState /> : <SalesTrendChart data={data} metric={metric} />}
    </SectionCard>
  )
}

function CustomerSection() {
  const { data, error, loading, reload } = useApi(getCustomerInsights, [])
  return (
    <SectionCard title="Customer Insights Snapshot" description="A compact view of purchasing engagement. Open Customer Insights for full metric definitions.">
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !data ? <EmptyState /> : <CustomerInsights data={data} />}
    </SectionCard>
  )
}

function PromotionSection() {
  const { data, error, loading, reload } = useApi(getPromotions, [])
  const promotions = data?.slice(0, 3)
  return (
    <SectionCard
      title="Promotions Snapshot"
      description="The three most-used offers. Associated revenue is intentionally not aggregated here."
      action={<span className="section-label">Top 3 by usage</span>}
    >
      {loading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={reload} /> : !promotions?.length ? <EmptyState /> : (
        <div className="dashboard-promotion-list">
          {promotions.map((promotion, index) => (
            <article key={promotion.promotion_id}>
              <span className="promotion-rank">{index + 1}</span>
              <div>
                <strong>{promotion.promo_name}</strong>
                <small>{promotion.manufacturer} {promotion.phone_model} · {promotion.promo_code}</small>
              </div>
              <div><span>Uses</span><strong>{formatNumber(promotion.times_used)}</strong></div>
              <div><span>Discounts</span><strong>{formatCurrency(promotion.total_discount_amount, 0)}</strong></div>
            </article>
          ))}
        </div>
      )}
    </SectionCard>
  )
}

export default function Dashboard({ onCompare }) {
  return (
    <div className="page-container">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Executive overview</span>
          <h1>Sales performance at a glance</h1>
          <p>Live insights across customers, phones, manufacturers, and promotions.</p>
        </div>
        <div className="live-data-chip"><span /> Live dataset</div>
      </div>

      <KpiSection />

      <div className="dashboard-grid dashboard-grid--hero">
        <TopPhonesSection />
        <TopPhoneFeature onCompare={onCompare} />
      </div>

      <div className="dashboard-grid dashboard-grid--analytics">
        <ManufacturerSection />
        <TrendSection />
      </div>

      <CustomerSection />
      <PromotionSection />
    </div>
  )
}
