export default function KpiCard({ label, value, detail, tone = 'blue' }) {
  return (
    <article className={`kpi-card kpi-card--${tone}`}>
      <div className="kpi-card__topline">
        <span>{label}</span>
        <span className="kpi-card__mark" aria-hidden="true" />
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  )
}
