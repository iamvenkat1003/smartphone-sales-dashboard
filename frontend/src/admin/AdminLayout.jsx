import { useAuth } from '../auth/AuthContext'

const adminNavigation = [
  { route: 'admin', label: 'Overview', icon: '⌂' },
  { route: 'admin/phones', label: 'Phones', icon: '▯' },
  { route: 'admin/promotions', label: 'Promotions', icon: '%' },
  { route: 'admin/customers', label: 'Customers', icon: '◎' },
  { route: 'admin/purchases', label: 'Purchases', icon: '↗' },
  { route: 'admin/admins', label: 'Admins', icon: '◇' },
]

export default function AdminLayout({ route, onNavigate, children }) {
  const auth = useAuth()
  const logout = () => {
    auth.logout()
    onNavigate('dashboard')
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <button className="admin-brand" type="button" onClick={() => onNavigate('admin')}>
          <span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>
          <div><strong>Sales Analytics</strong><small>Admin console</small></div>
        </button>
        <nav aria-label="Admin navigation">
          {adminNavigation.map((item) => (
            <button className={route === item.route ? 'is-active' : ''} key={item.route} type="button" onClick={() => onNavigate(item.route)}>
              <span aria-hidden="true">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="admin-profile">
          <span>{auth.currentAdmin.first_name.slice(0, 1)}{auth.currentAdmin.last_name.slice(0, 1)}</span>
          <div><strong>{auth.currentAdmin.first_name} {auth.currentAdmin.last_name}</strong><small>{auth.currentAdmin.email}</small></div>
        </div>
        <button className="admin-logout" type="button" onClick={logout}>Log out</button>
        <button className="admin-public-link" type="button" onClick={() => onNavigate('dashboard')}>← Public dashboard</button>
      </aside>
      <main className="admin-main">{children}</main>
    </div>
  )
}
