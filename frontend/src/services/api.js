export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let authToken = null

export function setAuthToken(token) {
  authToken = token || null
}

async function request(path, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('Unable to reach analytics API.')
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // Keep the useful HTTP fallback if the response is not JSON.
    }
    throw new ApiError(detail, response.status)
  }

  return response.json()
}

export function getHealth() {
  return request('/health')
}

export function getKPIs() {
  return request('/api/analytics/kpis')
}

export function getTopPhones(metric = 'units', limit = 5) {
  const params = new URLSearchParams({ metric, limit: String(limit) })
  return request(`/api/analytics/top-phones?${params}`)
}

export function getManufacturers() {
  return request('/api/analytics/manufacturers')
}

export function getSalesTrend() {
  return request('/api/analytics/sales-trend')
}

export function getPromotions() {
  return request('/api/analytics/promotions')
}

export function getCustomerInsights() {
  return request('/api/analytics/customers')
}

export function getPhones(filters = {}) {
  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.manufacturerId) {
    params.set('manufacturer_id', String(filters.manufacturerId))
  }
  if (filters.activeOnly !== undefined) {
    params.set('active_only', String(filters.activeOnly))
  }
  const query = params.toString()
  return request(`/api/phones${query ? `?${query}` : ''}`)
}

export function getPhone(id) {
  return request(`/api/phones/${encodeURIComponent(id)}`)
}

export function comparePhones(ids) {
  const params = new URLSearchParams()
  ids.forEach((id) => params.append('ids', String(id)))
  return request(`/api/phones/compare?${params}`)
}

export function loginAdmin(email, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getCurrentAdmin() {
  return request('/api/auth/me')
}

export function getAdminOverview() {
  return request('/api/admin/overview')
}

export function getAdminManufacturers() {
  return request('/api/admin/manufacturers')
}

export function getAdminPhones() {
  return request('/api/admin/phones')
}

export function createAdminPhone(payload) {
  return request('/api/admin/phones', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminPhone(id, payload) {
  return request(`/api/admin/phones/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function setAdminPhoneStatus(id, isActive) {
  return request(`/api/admin/phones/${id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) })
}

export function getAdminPromotions() {
  return request('/api/admin/promotions')
}

export function createAdminPromotion(payload) {
  return request('/api/admin/promotions', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminPromotion(id, payload) {
  return request(`/api/admin/promotions/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function setAdminPromotionStatus(id, isActive) {
  return request(`/api/admin/promotions/${id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) })
}

export function getAdminCustomers({ page = 1, pageSize = 25, search = '' } = {}) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  return request(`/api/admin/customers?${params}`)
}

export function updateAdminCustomer(id, payload) {
  return request(`/api/admin/customers/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function getAdminPurchases({ page = 1, pageSize = 25, search = '' } = {}) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  return request(`/api/admin/purchases?${params}`)
}

export function getAdminPurchase(id) {
  return request(`/api/admin/purchases/${id}`)
}

export function createAdminPurchase(payload) {
  return request('/api/admin/purchases', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminPurchase(id, payload) {
  return request(`/api/admin/purchases/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function getAdmins() {
  return request('/api/admin/admins')
}

export function createAdminAccount(payload) {
  return request('/api/admin/admins', { method: 'POST', body: JSON.stringify(payload) })
}

export function setAdminAccountStatus(id, isActive) {
  return request(`/api/admin/admins/${id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) })
}
