import KpiCard from '../components/KpiCard'
import SectionCard from '../components/SectionCard'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useApi } from '../hooks/useApi'
import { getCustomerInsights } from '../services/api'
import { formatNumber } from '../utils/formatters'

function PercentagePanel({ title, value, percentage, description, tone }) {
  return (
    <article className={`percentage-panel percentage-panel--${tone}`}>
      <div className="percentage-panel__header">
        <div><span>{title}</span><strong>{formatNumber(value)}</strong></div>
        <b>{percentage}%</b>
      </div>
      <div className="percentage-track"><span style={{ width: `${Math.min(percentage, 100)}%` }} /></div>
      <p>{description}</p>
    </article>
  )
}

export default function CustomerInsightsPage() {
  const customers = useApi(getCustomerInsights, [])
  const data = customers.data
  const multiPhonePercentage = data
    ? Number(((data.multi_phone_customers / data.total_customers) * 100).toFixed(2))
    : 0

  return (
    <div className="page-container customers-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Purchase behavior</span>
          <h1>Customer insights</h1>
          <p>Aggregate purchasing patterns across the complete customer dataset.</p>
        </div>
        <span className="comparison-limit">Behavioral analytics</span>
      </div>

      {customers.loading ? <LoadingState label="Loading customer insights…" compact /> : customers.error ? <ErrorState error={customers.error} onRetry={customers.reload} compact /> : !data ? <EmptyState /> : (
        <>
          <div className="kpi-grid customer-kpis">
            <KpiCard label="Total Customers" value={formatNumber(data.total_customers)} detail="Customers represented in the dataset" tone="indigo" />
            <KpiCard label="Repeat Customers" value={formatNumber(data.repeat_customers)} detail={`${data.repeat_customer_percentage}% made multiple purchases`} tone="sky" />
            <KpiCard label="Multi-Phone Customers" value={formatNumber(data.multi_phone_customers)} detail={`${multiPhonePercentage}% bought distinct phone models`} tone="emerald" />
            <KpiCard label="Average Units / Customer" value={Number(data.average_units_per_customer).toFixed(2)} detail="Units across the full customer base" tone="amber" />
          </div>

          <div className="customer-layout">
            <SectionCard title="Customer Engagement" description="How much of the customer base demonstrates repeat or varied purchasing behavior.">
              <div className="percentage-grid">
                <PercentagePanel
                  title="Repeat Customers"
                  value={data.repeat_customers}
                  percentage={data.repeat_customer_percentage}
                  description="Customers with more than one purchase transaction."
                  tone="indigo"
                />
                <PercentagePanel
                  title="Multi-Phone Customers"
                  value={data.multi_phone_customers}
                  percentage={multiPhonePercentage}
                  description="Customers who purchased more than one distinct phone model."
                  tone="sky"
                />
                <PercentagePanel
                  title="Multi-Brand Customers"
                  value={data.multi_manufacturer_customers}
                  percentage={data.multi_manufacturer_percentage}
                  description="Customers whose purchases include phones from multiple manufacturers."
                  tone="emerald"
                />
              </div>
            </SectionCard>

            <aside className="insight-definition-card">
              <span className="eyebrow">Metric clarity</span>
              <h2>Multi-brand, not brand switching</h2>
              <p>This metric identifies customers who purchased from more than one manufacturer. It does not infer chronological switching or customer intent.</p>
              <div><strong>{data.multi_manufacturer_percentage}%</strong><span>of all customers</span></div>
            </aside>
          </div>

          <div className="data-scope-note">
            <strong>Current scope</strong>
            <p>The public analytics API exposes aggregate purchasing behavior. Demographic fields are not included, so this demo does not invent demographic insights.</p>
          </div>
        </>
      )}
    </div>
  )
}
