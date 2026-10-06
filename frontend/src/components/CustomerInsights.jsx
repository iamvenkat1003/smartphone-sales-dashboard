import { formatNumber } from '../utils/formatters'

const insights = (data) => [
  {
    label: 'Repeat Customers',
    value: formatNumber(data.repeat_customers),
    meta: `${data.repeat_customer_percentage}% of customers`,
    tone: 'indigo',
  },
  {
    label: 'Multi-Phone Customers',
    value: formatNumber(data.multi_phone_customers),
    meta: `${((data.multi_phone_customers / data.total_customers) * 100).toFixed(1)}% of customers`,
    tone: 'sky',
  },
  {
    label: 'Multi-Brand Customers',
    value: formatNumber(data.multi_manufacturer_customers),
    meta: `${data.multi_manufacturer_percentage}% of customers`,
    tone: 'emerald',
  },
  {
    label: 'Average Units / Customer',
    value: Number(data.average_units_per_customer).toFixed(2),
    meta: 'Across the full customer base',
    tone: 'amber',
  },
]

export default function CustomerInsights({ data }) {
  return (
    <div className="insight-grid">
      {insights(data).map((item) => (
        <article className={`insight-card insight-card--${item.tone}`} key={item.label}>
          <span className="insight-card__icon" aria-hidden="true" />
          <div>
            <p>{item.label}</p>
            <strong>{item.value}</strong>
            <small>{item.meta}</small>
          </div>
        </article>
      ))}
    </div>
  )
}
