import { API_BASE_URL } from '../services/api'

const navigation = [
  { label: 'Dashboard', route: 'dashboard' },
  { label: 'Phones', route: 'phones' },
  { label: 'Compare Phones', route: 'compare' },
  { label: 'Promotions', route: 'promotions' },
  { label: 'Customer Insights', route: 'customers' },
]

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  )
}

export default function Layout({ route, onNavigate, apiStatus, currentAdmin, children }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__inner">
          <button className="brand" type="button" onClick={() => onNavigate('dashboard')}>
            <BrandMark />
            <span>
              <strong>Smartphone Sales</strong>
              <small>Analytics</small>
            </span>
          </button>

          <nav aria-label="Primary navigation">
            {navigation.map((item) => (
              <button
                className={route === item.route ? 'is-active' : ''}
                key={item.route}
                type="button"
                onClick={() => onNavigate(item.route)}
              >
                {item.label}
              </button>
            ))}
            <button
              className={route.startsWith('admin') ? 'is-active' : ''}
              type="button"
              onClick={() => onNavigate(currentAdmin ? 'admin' : 'admin/login')}
            >
              {currentAdmin ? 'Admin Panel' : 'Admin Login'}
            </button>
          </nav>

          <a
            className={`api-status api-status--${apiStatus}`}
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            title="Open FastAPI documentation"
          >
            <span className="api-status__dot" />
            <span>
              <small>API Status</small>
              <strong>{apiStatus === 'online' ? 'Online' : apiStatus === 'offline' ? 'Offline' : 'Checking'}</strong>
            </span>
          </a>
        </div>
      </header>

      <main>{children}</main>

      <footer>
        <span>Smartphone Sales Analytics</span>
        <span>Live data from FastAPI + SQLite</span>
      </footer>
    </div>
  )
}
