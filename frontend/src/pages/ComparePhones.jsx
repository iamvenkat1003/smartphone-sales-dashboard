import { useEffect, useMemo, useState } from 'react'

import PhoneArtwork from '../components/PhoneArtwork'
import SectionCard from '../components/SectionCard'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useApi } from '../hooks/useApi'
import { comparePhones, getPhones } from '../services/api'
import { formatCompactCurrency, formatCurrency, formatNumber } from '../utils/formatters'

function PhoneSelect({ index, value, phones, selections, onChange, optional }) {
  const usedByOthers = selections.filter((id, selectionIndex) => selectionIndex !== index && id)
  return (
    <label className="phone-select">
      <span>Phone {index + 1}{optional ? ' (optional)' : ''}</span>
      <select value={value} onChange={(event) => onChange(index, event.target.value)}>
        <option value="">Select a phone</option>
        {phones.map((phone) => (
          <option
            key={phone.phone_id}
            value={phone.phone_id}
            disabled={usedByOthers.includes(String(phone.phone_id))}
          >
            {phone.manufacturer_name} {phone.model_name} · {phone.storage_gb} GB
          </option>
        ))}
      </select>
    </label>
  )
}

function MetricRow({ label, value, best }) {
  return (
    <div className={`comparison-metric ${best ? 'comparison-metric--best' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {best && <small>Highest</small>}
    </div>
  )
}

function ComparisonCard({ phone, bestValues }) {
  return (
    <article className="comparison-card">
      <div className="comparison-card__visual">
        <PhoneArtwork imagePath={phone.image_path} modelName={phone.model_name} size="large" />
      </div>
      <div className="comparison-card__header">
        <p>{phone.manufacturer}</p>
        <h2>{phone.model_name}</h2>
        <div className="spec-pills">
          <span>{phone.storage_gb} GB</span>
          <span>{phone.ram_gb} GB RAM</span>
          <span>{phone.operating_system}</span>
        </div>
      </div>
      <dl className="phone-specs">
        <div><dt>Release date</dt><dd>{phone.release_date || 'Not available'}</dd></div>
        <div><dt>Launch price</dt><dd>{formatCurrency(phone.launch_price)}</dd></div>
      </dl>
      <div className="comparison-metrics">
        <MetricRow label="Weighted avg. selling price" value={formatCurrency(phone.average_selling_price)} best={phone.average_selling_price === bestValues.average_selling_price} />
        <MetricRow label="Units sold" value={formatNumber(phone.units_sold)} best={phone.units_sold === bestValues.units_sold} />
        <MetricRow label="Revenue" value={formatCompactCurrency(phone.revenue)} best={phone.revenue === bestValues.revenue} />
        <MetricRow label="Transactions" value={formatNumber(phone.transactions)} best={phone.transactions === bestValues.transactions} />
        <MetricRow label="Promotion uses" value={formatNumber(phone.promotion_uses)} best={phone.promotion_uses === bestValues.promotion_uses} />
      </div>
    </article>
  )
}

export default function ComparePhones() {
  const phoneList = useApi(() => getPhones({ activeOnly: true }), [])
  const [selections, setSelections] = useState(['', '', ''])
  const [visibleCount, setVisibleCount] = useState(2)
  const [comparison, setComparison] = useState(null)
  const [compareError, setCompareError] = useState(null)
  const [comparing, setComparing] = useState(false)

  const runComparison = async (ids) => {
    setComparing(true)
    setCompareError(null)
    try {
      setComparison(await comparePhones(ids))
    } catch (error) {
      setComparison(null)
      setCompareError(error)
    } finally {
      setComparing(false)
    }
  }

  useEffect(() => {
    if (phoneList.data?.length >= 2 && selections.every((value) => !value)) {
      const initial = phoneList.data.slice(0, 2).map((phone) => String(phone.phone_id))
      setSelections([...initial, ''])
      runComparison(initial)
    }
  }, [phoneList.data])

  const selectedIds = selections.slice(0, visibleCount).filter(Boolean)
  const canCompare = selectedIds.length >= 2 && new Set(selectedIds).size === selectedIds.length

  const bestValues = useMemo(() => {
    const metrics = ['average_selling_price', 'units_sold', 'revenue', 'transactions', 'promotion_uses']
    return Object.fromEntries(
      metrics.map((metric) => [metric, Math.max(...(comparison || []).map((phone) => Number(phone[metric] || 0)))]),
    )
  }, [comparison])

  const updateSelection = (index, value) => {
    setSelections((current) => current.map((item, itemIndex) => itemIndex === index ? value : item))
    setComparison(null)
    setCompareError(null)
  }

  const submit = (event) => {
    event.preventDefault()
    if (canCompare) runComparison(selectedIds)
  }

  return (
    <div className="page-container compare-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Side-by-side analysis</span>
          <h1>Compare phone performance</h1>
          <p>Evaluate product specifications and real sales results for two or three phones.</p>
        </div>
        <span className="comparison-limit">2–3 phones</span>
      </div>

      <SectionCard
        title="Choose phones"
        description="Each configuration can be selected once. Add a third phone when needed."
        className="selector-section"
      >
        {phoneList.loading ? <LoadingState label="Loading phone catalog…" compact /> : phoneList.error ? <ErrorState error={phoneList.error} onRetry={phoneList.reload} compact /> : !phoneList.data?.length ? <EmptyState message="No active phones are available to compare." /> : (
          <form className="comparison-form" onSubmit={submit}>
            <div className={`selector-grid selector-grid--${visibleCount}`}>
              {Array.from({ length: visibleCount }, (_, index) => (
                <PhoneSelect
                  key={index}
                  index={index}
                  value={selections[index]}
                  phones={phoneList.data}
                  selections={selections.slice(0, visibleCount)}
                  onChange={updateSelection}
                  optional={index === 2}
                />
              ))}
            </div>
            <div className="comparison-actions">
              {visibleCount === 2 ? (
                <button className="button button--quiet" type="button" onClick={() => setVisibleCount(3)}>
                  <span aria-hidden="true">＋</span> Add third phone
                </button>
              ) : (
                <button
                  className="button button--quiet"
                  type="button"
                  onClick={() => {
                    setVisibleCount(2)
                    setSelections((current) => [current[0], current[1], ''])
                    setComparison(null)
                  }}
                >
                  Remove third phone
                </button>
              )}
              <button className="button button--primary" type="submit" disabled={!canCompare || comparing}>
                {comparing ? 'Comparing…' : 'Compare selected phones'}
              </button>
            </div>
          </form>
        )}
      </SectionCard>

      {comparing ? (
        <LoadingState label="Building comparison…" />
      ) : compareError ? (
        <ErrorState error={compareError} onRetry={() => canCompare && runComparison(selectedIds)} />
      ) : comparison?.length ? (
        <div className={`comparison-grid comparison-grid--${comparison.length}`}>
          {comparison.map((phone) => (
            <ComparisonCard phone={phone} bestValues={bestValues} key={phone.phone_id} />
          ))}
        </div>
      ) : (
        <EmptyState message="Select at least two phones, then run the comparison." />
      )}
    </div>
  )
}
