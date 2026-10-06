import AdminLayout from './AdminLayout'
import {
  AdminAccountsPage,
  AdminCustomersPage,
  AdminOverviewPage,
  AdminPhonesPage,
  AdminPromotionsPage,
  AdminPurchasesPage,
} from './AdminPages'

export default function AdminApp({ route, onNavigate }) {
  const pages = {
    admin: <AdminOverviewPage onNavigate={onNavigate} />,
    'admin/phones': <AdminPhonesPage />,
    'admin/promotions': <AdminPromotionsPage />,
    'admin/customers': <AdminCustomersPage />,
    'admin/purchases': <AdminPurchasesPage />,
    'admin/admins': <AdminAccountsPage />,
  }

  return <AdminLayout route={route} onNavigate={onNavigate}>{pages[route] || pages.admin}</AdminLayout>
}
