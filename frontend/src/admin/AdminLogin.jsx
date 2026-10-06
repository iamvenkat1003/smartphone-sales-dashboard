import { useState } from 'react'

import { useAuth } from '../auth/AuthContext'

export default function AdminLogin({ onSuccess, onBack }) {
  const auth = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await auth.login(email, password)
      onSuccess()
    } catch (requestError) {
      setError(requestError.status === 401 ? 'Invalid email or password.' : requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="admin-login-page">
      <button className="admin-login-back" type="button" onClick={onBack}>← Public dashboard</button>
      <div className="admin-login-panel">
        <div className="admin-login-brand">
          <span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>
          <div><strong>Smartphone Sales</strong><small>Administration</small></div>
        </div>
        <span className="eyebrow">Protected access</span>
        <h1>Welcome back</h1>
        <p>Sign in with an active administrator account to manage dashboard data.</p>

        {auth.isAuthenticated ? (
          <div className="existing-session">
            <span>Active session</span>
            <strong>{auth.currentAdmin.first_name} {auth.currentAdmin.last_name}</strong>
            <button className="button button--primary" type="button" onClick={onSuccess}>Enter admin panel</button>
          </div>
        ) : (
          <form className="admin-login-form" onSubmit={submit}>
            <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" required /></label>
            <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="button button--primary" type="submit" disabled={submitting}>{submitting ? 'Signing in…' : 'Sign in to admin'}</button>
          </form>
        )}
        <small className="admin-login-note">Public analytics remain available without signing in.</small>
      </div>
      <div className="admin-login-aside">
        <span>ADMIN CONSOLE</span>
        <h2>Manage the data behind the dashboard.</h2>
        <ul><li>Secure JWT-protected access</li><li>Phone and promotion management</li><li>Customer and purchase operations</li></ul>
      </div>
    </div>
  )
}
