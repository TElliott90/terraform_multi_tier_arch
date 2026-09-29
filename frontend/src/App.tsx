import { useEffect, useState } from 'react'
import LoginPage from './pages/LoginPage'
import RegistrationPage from './pages/RegistrationPage'
import { request } from './api'
import type { User } from './api'
import './App.css'

function App() {
  const [page, setPage] = useState(window.location.hash)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [signingOut, setSigningOut] = useState(false)
  useEffect(() => {
    const navigate = () => setPage(window.location.hash)
    window.addEventListener('hashchange', navigate)
    request<{ user: User | null }>('me').then(data => setUser(data.user))
      .catch(() => setError('Unable to connect to the server. Make sure the backend is running, then refresh.'))
      .finally(() => setLoading(false))
    return () => window.removeEventListener('hashchange', navigate)
  }, [])
  async function logout() {
    setSigningOut(true)
    setError('')
    try { await request('logout', {}); setUser(null); window.location.hash = 'login' }
    catch { setError('Could not sign out. Please try again.') }
    finally { setSigningOut(false) }
  }
  function authenticated(value: User) { setError(''); setUser(value) }
  return <div className="app-shell">
    <aside className="brand-panel">
      <a className="brand" href="#login"><span className="brand-mark" aria-hidden="true">n</span>nest<span className="brand-dot">.</span></a>
      <div className="brand-story"><p className="eyebrow">A LITTLE SPACE FOR YOU</p><h2>Good things<br />start here.</h2><p>One account. Your own corner.<br />Come on in and make it yours.</p><div className="illustration" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="tile tile-back" /><div className="tile tile-front"><span>✳</span></div><span className="spark">✦</span><span className="small-dot" /></div></div>
      <p className="brand-footer">Simple. Personal. Yours.</p>
    </aside>
    <main><div className="auth-card">
      {error && <p className="error" role="alert">{error}</p>}
      {loading ? <p role="status">Opening your space…</p> : user ? <><div className="success-icon" aria-hidden="true">✓</div><p className="eyebrow">YOU’RE ALL SET</p><h1>Hello, {user.name}.</h1><p className="intro">You’re signed in as <strong>{user.email}</strong>.</p><button className="primary" onClick={logout} disabled={signingOut}>{signingOut ? 'Signing out…' : 'Sign out'} <span aria-hidden="true">→</span></button></> : page === '#register' ? <RegistrationPage key="register" onAuthenticated={authenticated} /> : <LoginPage key="login" onAuthenticated={authenticated} />}
    </div><footer className="page-footer">A fresh start, a familiar place.</footer></main>
  </div>
}
export default App
