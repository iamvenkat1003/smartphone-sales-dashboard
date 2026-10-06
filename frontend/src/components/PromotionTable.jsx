import { formatCurrency, formatNumber } from '../utils/formatters'

export default function PromotionTable({ data }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Promotion</th>
            <th>Phone</th>
            <th>Uses</th>
            <th>Total discount</th>
            <th>Associated revenue</th>
          </tr>
        </thead>
        <tbody>
          {data.map((promotion) => (
            <tr key={promotion.promotion_id}>
              <td>
                <strong>{promotion.promo_name}</strong>
                <span className="code-pill">{promotion.promo_code}</span>
              </td>
              <td>
                <strong>{promotion.phone_model}</strong>
                <small>{promotion.manufacturer}</small>
              </td>
              <td>{formatNumber(promotion.times_used)}</td>
              <td>{formatCurrency(promotion.total_discount_amount, 0)}</td>
              <td>{formatCurrency(promotion.associated_revenue, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
