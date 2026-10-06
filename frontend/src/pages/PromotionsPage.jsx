import { useMemo, useState } from 'react'

import { PromotionUsageChart } from '../components/AnalyticsCharts'
import KpiCard from '../components/KpiCard'
import PromotionTable from '../components/PromotionTable'
import SectionCard from '../components/SectionCard'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useApi } from '../hooks/useApi'
import { getPromotions } from '../services/api'
import { formatCurrency, formatNumber } from '../utils/formatters'

const sorters = {
  usage: (a, b) => b.times_used - a.times_used,
  discount: (a, b) => b.total_discount_amount - a.total_discount_amount,
  revenue: (a, b) => b.associated_revenue - a.associated_revenue,
}

export default function PromotionsPage() {
  const promotions = useApi(getPromotions, [])
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('usage')

  const summary = useMemo(() => {
    if (!promotions.data?.length) return null
    const uses = promotions.data.reduce((total, item) => total + item.times_used, 0)
    const discounts = promotions.data.reduce((total, item) => total + item.total_discount_amount, 0)
    const leader = [...promotions.data].sort(sorters.usage)[0]
    return { uses, discounts, leader }
  }, [promotions.data])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return [...(promotions.data || [])]
      .filter((item) => !term || `${item.promo_name} ${item.promo_code} ${item.manufacturer} ${item.phone_model}`.toLowerCase().includes(term))
      .sort(sorters[sort])
  }, [promotions.data, search, sort])

  const topPromotions = useMemo(
    () => [...(promotions.data || [])].sort(sorters.usage).slice(0, 8),
    [promotions.data],
  )

  return (
    <div className="page-container promotions-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Offer analytics</span>
          <h1>Promotion performance</h1>
          <p>Understand offer adoption, applied discounts, and promotion-associated sales.</p>
        </div>
        <span className="comparison-limit">Promotion-level analysis</span>
      </div>

      {promotions.loading ? <LoadingState label="Loading promotion analytics…" compact /> : promotions.error ? <ErrorState error={promotions.error} onRetry={promotions.reload} compact /> : !summary ? <EmptyState /> : (
        <>
          <div className="kpi-grid promotion-kpis">
            <KpiCard label="Promotions Tracked" value={formatNumber(promotions.data.length)} detail="Offers in the analytics dataset" tone="indigo" />
            <KpiCard label="Promotion Applications" value={formatNumber(summary.uses)} detail="Counts promotion-to-purchase uses" tone="sky" />
            <KpiCard label="Discounts Applied" value={formatCurrency(summary.discounts, 0)} detail="Sum of recorded discount amounts" tone="emerald" />
            <KpiCard label="Most-Used Promotion" value={formatNumber(summary.leader.times_used)} detail={summary.leader.promo_name} tone="amber" />
          </div>

          <div className="promotion-disclaimer">
            <span aria-hidden="true">i</span>
            <p><strong>How to read associated revenue:</strong> a purchase may use two promotions, so the same purchase revenue can appear under more than one offer. It is intentionally not presented as total company revenue.</p>
          </div>

          <SectionCard title="Top Promotions" description="The eight most-used promotions across completed purchases." action={<span className="section-label">Ranked by usage</span>}>
            <PromotionUsageChart data={topPromotions} />
          </SectionCard>

          <SectionCard title="Promotion Detail" description="Filter and sort the complete promotion-level dataset.">
            <div className="catalog-toolbar promotion-toolbar">
              <label className="search-field">
                <span aria-hidden="true">⌕</span>
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search promotions…" aria-label="Search promotions" />
              </label>
              <label className="filter-field">
                <span>Sort by</span>
                <select value={sort} onChange={(event) => setSort(event.target.value)}>
                  <option value="usage">Most used</option>
                  <option value="discount">Largest discount total</option>
                  <option value="revenue">Associated revenue</option>
                </select>
              </label>
              <span className="result-count">{filtered.length} promotions</span>
            </div>
            {filtered.length ? <PromotionTable data={filtered} /> : <EmptyState message="No promotions match this search." />}
          </SectionCard>
        </>
      )}
    </div>
  )
}
