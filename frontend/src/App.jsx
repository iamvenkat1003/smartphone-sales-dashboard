import { useEffect, useState } from 'react'

import AdminApp from './admin/AdminApp'
import AdminLogin from './admin/AdminLogin'
import { useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import ComparePhones from './pages/ComparePhones'
import CustomerInsightsPage from './pages/CustomerInsightsPage'
import Dashboard from './pages/Dashboard'
import PhonesPage from './pages/PhonesPage'
import PromotionsPage from './pages/PromotionsPage'
import { getHealth } from './services/api'

function getRoute() {
  const route = window.location.hash.replace(/^#\/?/, '')
  if (route === 'admin/login' || route === 'admin') return route
  if (['phones', 'promotions', 'customers', 'purchases', 'admins'].some(
    (page) => route === `admin/${page}`,
  )) return route
  return ['phones', 'compare', 'promotions', 'customers'].includes(route)
    ? route
    : 'dashboard'
}

export default function App() {
  const [route, setRoute] = useState(getRoute)
  const [apiStatus, setApiStatus] = useState('checking')
  const auth = useAuth()

  useEffect(() => {
    const updateRoute = () => setRoute(getRoute())
    window.addEventListener('hashchange', updateRoute)
    return () => window.removeEventListener('hashchange', updateRoute)
  }, [])

  useEffect(() => {
    let active = true
    getHealth()
      .then(() => active && setApiStatus('online'))
      .catch(() => active && setApiStatus('offline'))
    return () => {
      active = false
    }
  }, [route])

  const navigate = (nextRoute) => {
    window.location.hash = nextRoute === 'dashboard' ? '/' : `/${nextRoute}`
    setRoute(nextRoute)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    if (route.startsWith('admin') && route !== 'admin/login' && !auth.loading && !auth.isAuthenticated) {
      navigate('admin/login')
    }
  }, [route, auth.loading, auth.isAuthenticated])

  if (route === 'admin/login') {
    return <AdminLogin onSuccess={() => navigate('admin')} onBack={() => navigate('dashboard')} />
  }

  if (route.startsWith('admin')) {
    if (auth.loading || !auth.isAuthenticated) return <div className="admin-auth-loading"><span className="spinner" /> Verifying admin session…</div>
    return <AdminApp route={route} onNavigate={navigate} />
  }

  return (
    <Layout route={route} onNavigate={navigate} apiStatus={apiStatus} currentAdmin={auth.currentAdmin}>
      {route === 'dashboard' && <Dashboard onCompare={() => navigate('compare')} />}
      {route === 'phones' && <PhonesPage />}
      {route === 'compare' && <ComparePhones />}
      {route === 'promotions' && <PromotionsPage />}
      {route === 'customers' && <CustomerInsightsPage />}
    </Layout>
  )
}
