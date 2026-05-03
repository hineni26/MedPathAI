import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { LogIn, ShieldCheck, UserCog } from 'lucide-react'
import { loginUser, markRegistered, setAccessToken, setUserId } from '../../api/auth'
import { loginOfficer } from '../../api/pfl'
import { setOfficerToken } from '../../api/session'
import { useUserStore } from '../../store/userStore'
import { useUIStore } from '../../store/uiStore'
import { Spinner } from '../../components/ui'

export default function Login() {
  const navigate = useNavigate()
  const toast = useUIStore((s) => s.toast)
  const setStoreUserId = useUserStore((s) => s.setUserId)
  const setProfile = useUserStore((s) => s.setProfile)
  const setFinancials = useUserStore((s) => s.setFinancials)
  const setDocuments = useUserStore((s) => s.setDocuments)

  const [form, setForm] = useState({ email: '', password: '' })
  const [mode, setMode] = useState('patient')
  const [loading, setLoading] = useState(false)

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)

    try {
      if (mode === 'admin') {
        const data = await loginOfficer({
          email: form.email.trim().toLowerCase(),
          password: form.password,
        })

        setOfficerToken(data.access_token)
        toast('Administrator login successful', 'success')
        navigate('/admin')
        return
      }

      const data = await loginUser({
        email: form.email.trim().toLowerCase(),
        password: form.password,
      })

      setUserId(data.user_id)
      setAccessToken(data.access_token)
      setStoreUserId(data.user_id)
      setProfile(data.profile || null)
      setFinancials(data.financials || null)
      setDocuments(data.documents || [])
      markRegistered()
      toast('Welcome back', 'success')
      navigate('/chat')
    } catch (err) {
      toast(err.message || 'Login failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-content" style={{ maxWidth: 520 }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'var(--text-2xl)',
          fontWeight: 700,
          marginBottom: 6,
        }}>
          Log in to MedPath AI
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
          Continue with an existing profile, documents, chat context, and financing eligibility.
        </p>
      </div>

      <form className="card" style={{ padding: 'var(--space-8)' }} onSubmit={handleSubmit}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
          marginBottom: 'var(--space-6)',
        }}>
          <button
            type="button"
            className={`btn ${mode === 'patient' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setMode('patient')}
          >
            <LogIn size={16} /> Patient
          </button>
          <button
            type="button"
            className={`btn ${mode === 'admin' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setMode('admin')}
          >
            <UserCog size={16} /> Administrator
          </button>
        </div>

        <div style={{ marginBottom: 'var(--space-5)' }}>
          <label className="form-label">Email</label>
          <input
            className="form-input"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>

        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label className="form-label">Password</label>
          <input
            className="form-input"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            placeholder="Enter your password"
            required
          />
        </div>

        <div style={{
          display: 'flex',
          gap: 8,
          padding: '10px 14px',
          background: 'var(--teal-50)',
          border: '1px solid var(--teal-100)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-6)',
        }}>
          <ShieldCheck size={15} color="var(--teal-700)" style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--teal-800)' }}>
            {mode === 'admin'
              ? 'Administrator credentials open the PFL officer dashboard for reviewing loan applications.'
              : 'Passwords are checked using a salted one-way hash. Your raw password is never stored.'}
          </p>
        </div>

        <button className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%' }}>
          {loading
            ? <><Spinner size={16} color="#fff" /> Logging in...</>
            : mode === 'admin'
              ? <><UserCog size={17} /> Login as administrator</>
              : <><LogIn size={17} /> Log in</>}
        </button>

        {mode === 'patient' && (
          <p style={{ marginTop: 'var(--space-5)', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
            New here? <Link to="/register">Create your profile</Link>
          </p>
        )}
      </form>
    </div>
  )
}
