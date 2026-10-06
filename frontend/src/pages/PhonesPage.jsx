import { useMemo, useState } from 'react'

import PhoneArtwork from '../components/PhoneArtwork'
import SectionCard from '../components/SectionCard'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useApi } from '../hooks/useApi'
import { getPhone, getPhones } from '../services/api'
import { formatCompactCurrency, formatCurrency, formatNumber } from '../utils/formatters'

function PhoneDetail({ phone, onClose }) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        aria-labelledby="phone-detail-title"
        aria-modal="true"
        className="phone-detail-modal"
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button className="modal-close" type="button" onClick={onClose} aria-label="Close phone details">×</button>
        <div className="phone-detail-hero">
          <PhoneArtwork imagePath={phone.image_path} modelName={phone.model_name} size="large" />
          <div>
            <span className="eyebrow">{phone.manufacturer_name}</span>
            <h2 id="phone-detail-title">{phone.model_name}</h2>
            <p>{phone.storage_gb} GB storage · {phone.ram_gb} GB RAM · {phone.operating_system}</p>
            <div className="spec-pills">
              <span>Released {phone.release_date || 'N/A'}</span>
              <span>Launch {formatCurrency(phone.launch_price)}</span>
            </div>
          </div>
        </div>

        <div className="phone-detail-kpis">
          <div><span>Transactions</span><strong>{formatNumber(phone.transactions)}</strong></div>
          <div><span>Units sold</span><strong>{formatNumber(phone.units_sold)}</strong></div>
          <div><span>Revenue</span><strong>{formatCompactCurrency(phone.revenue)}</strong></div>
          <div><span>Weighted ASP</span><strong>{formatCurrency(phone.average_selling_price)}</strong></div>
        </div>

        <div className="phone-promotions">
          <div className="subsection-heading">
            <div><h3>Associated promotions</h3><p>Offers configured specifically for this phone.</p></div>
            <span>{phone.promotions.length}</span>
          </div>
          {phone.promotions.length ? (
            <div className="phone-promotion-list">
              {phone.promotions.map((promotion) => (
                <article key={promotion.promotion_id}>
                  <div>
                    <strong>{promotion.promo_name}</strong>
                    <span className="code-pill">{promotion.promo_code}</span>
                  </div>
                  <div><span>Offer</span><strong>{promotion.discount_type === 'PERCENTAGE' ? `${promotion.discount_value}%` : formatCurrency(promotion.discount_value)}</strong></div>
                  <div><span>Uses</span><strong>{formatNumber(promotion.times_used)}</strong></div>
                </article>
              ))}
            </div>
          ) : <EmptyState message="No promotions are associated with this phone." />}
        </div>
      </section>
    </div>
  )
}

export default function PhonesPage() {
  const catalog = useApi(() => getPhones({ activeOnly: true }), [])
  const [search, setSearch] = useState('')
  const [manufacturer, setManufacturer] = useState('all')
  const [detail, setDetail] = useState(null)
  const [detailError, setDetailError] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const manufacturers = useMemo(() => {
    const values = new Map()
    catalog.data?.forEach((phone) => values.set(phone.manufacturer_id, phone.manufacturer_name))
    return [...values.entries()].sort((a, b) => a[1].localeCompare(b[1]))
  }, [catalog.data])

  const phones = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (catalog.data || []).filter((phone) => {
      const matchesManufacturer = manufacturer === 'all' || String(phone.manufacturer_id) === manufacturer
      const matchesSearch = !term || `${phone.manufacturer_name} ${phone.model_name}`.toLowerCase().includes(term)
      return matchesManufacturer && matchesSearch
    })
  }, [catalog.data, manufacturer, search])

  const openDetails = async (phoneId) => {
    setDetailLoading(true)
    setDetailError(null)
    try {
      setDetail(await getPhone(phoneId))
    } catch (error) {
      setDetailError(error)
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <div className="page-container phones-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Product analytics</span>
          <h1>Phone performance catalog</h1>
          <p>Explore configurations, commercial performance, and associated promotions.</p>
        </div>
        <span className="comparison-limit">{formatNumber(catalog.data?.length || 0)} configurations</span>
      </div>

      <SectionCard title="Available phones" description="Search by manufacturer or model, then open a phone for deeper analytics." className="phone-catalog-section">
        <div className="catalog-toolbar">
          <label className="search-field">
            <span aria-hidden="true">⌕</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search phones…" aria-label="Search phones" />
          </label>
          <label className="filter-field">
            <span>Manufacturer</span>
            <select value={manufacturer} onChange={(event) => setManufacturer(event.target.value)}>
              <option value="all">All manufacturers</option>
              {manufacturers.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
            </select>
          </label>
          <span className="result-count">{phones.length} results</span>
        </div>

        {catalog.loading ? <LoadingState label="Loading phone catalog…" /> : catalog.error ? <ErrorState error={catalog.error} onRetry={catalog.reload} /> : !phones.length ? <EmptyState message="No phones match these filters." /> : (
          <div className="phone-card-grid">
            {phones.map((phone) => (
              <article className="phone-catalog-card" key={phone.phone_id}>
                <div className="phone-catalog-card__visual">
                  <PhoneArtwork imagePath={phone.image_path} modelName={phone.model_name} size="medium" />
                </div>
                <div className="phone-catalog-card__body">
                  <span>{phone.manufacturer_name}</span>
                  <h2>{phone.model_name}</h2>
                  <div className="spec-pills"><span>{phone.storage_gb} GB</span><span>{phone.ram_gb} GB RAM</span></div>
                  <dl>
                    <div><dt>Launch price</dt><dd>{formatCurrency(phone.launch_price)}</dd></div>
                    <div><dt>Weighted ASP</dt><dd>{formatCurrency(phone.average_selling_price)}</dd></div>
                    <div><dt>Units sold</dt><dd>{formatNumber(phone.units_sold)}</dd></div>
                    <div><dt>Revenue</dt><dd>{formatCompactCurrency(phone.revenue)}</dd></div>
                  </dl>
                  <button className="button button--quiet" type="button" onClick={() => openDetails(phone.phone_id)}>View analytics <span aria-hidden="true">→</span></button>
                </div>
              </article>
            ))}
          </div>
        )}
      </SectionCard>

      {detailLoading && <div className="modal-backdrop"><div className="modal-loading"><LoadingState label="Loading phone analytics…" /></div></div>}
      {detailError && <div className="floating-error"><ErrorState error={detailError} onRetry={() => setDetailError(null)} compact /></div>}
      {detail && <PhoneDetail phone={detail} onClose={() => setDetail(null)} />}
    </div>
  )
}
