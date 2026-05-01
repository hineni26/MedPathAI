import { useState, useEffect } from 'react'
import { ArrowRight } from 'lucide-react'
import { Spinner } from '../../components/ui'
import { BLOOD_GROUPS } from '../../utils/staticData'

const FALLBACK_CITIES = [
  'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai',
  'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow',
  'Nagpur', 'Indore', 'Coimbatore', 'Surat', 'Bhopal',
]

export default function StepHealthProfile({ form, update, onNext }) {
  const [cities, setCities]   = useState([])
  const [errors, setErrors]   = useState({})
  const [loadingCities, setLoadingCities] = useState(true)

  // Fetch cities from backend (sourced from Supabase / CSV)
  useEffect(() => {
    const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    fetch(`${BASE}/api/meta/cities`)
      .then((r) => {
        if (!r.ok) throw new Error('Cities endpoint unavailable')
        return r.json()
      })
      .then((data) => {
        const cityList = Array.isArray(data.cities) ? data.cities : []
        setCities(cityList.length ? cityList : FALLBACK_CITIES)
      })
      .catch(() => {
        setCities(FALLBACK_CITIES)
      })
      .finally(() => setLoadingCities(false))
  }, [])

  function validate() {
    const e = {}
    const isLoggedIn = !!localStorage.getItem('medpath_registered')
    if (!form.name.trim())  e.name   = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) e.email = 'Enter a valid email'
    if (!isLoggedIn && form.password.length < 8) e.password = 'Use at least 8 characters'
    if (!form.age || form.age < 1 || form.age > 120) e.age = 'Enter a valid age'
    if (!form.gender)       e.gender = 'Select a gender'
    if (!form.city)         e.city   = 'Select your city'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleNext() {
    if (validate()) onNext()
  }

  const field = (label, key, input) => (
    <div style={{ marginBottom: 'var(--space-5)' }}>
      <label className="form-label">{label}</label>
      {input}
      {errors[key] && (
        <p style={{ color: 'var(--color-danger)', fontSize: 'var(--text-xs)', marginTop: 4 }}>
          {errors[key]}
        </p>
      )}
    </div>
  )

  return (
    <div>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-lg)',
        fontWeight: 600,
        marginBottom: 'var(--space-6)',
      }}>
        Tell us about yourself
      </h3>

      {/* Name */}
      {field('Full name', 'name',
        <input
          className="form-input"
          placeholder="e.g. Priya Sharma"
          value={form.name}
          onChange={(e) => update({ name: e.target.value })}
          style={{ borderColor: errors.name ? 'var(--color-danger)' : undefined }}
        />
      )}

      {field('Email', 'email',
        <input
          className="form-input"
          type="email"
          autoComplete="email"
          placeholder="e.g. priya@example.com"
          value={form.email}
          onChange={(e) => update({ email: e.target.value })}
          style={{ borderColor: errors.email ? 'var(--color-danger)' : undefined }}
        />
      )}

      <div style={{ marginBottom: 'var(--space-5)' }}>
        <label className="form-label">
          Password <span style={{ color: 'var(--color-text-muted)', fontWeight: 400, textTransform: 'none' }}>
            {localStorage.getItem('medpath_registered') ? '(leave blank to keep current)' : ''}
          </span>
        </label>
        <input
          className="form-input"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={form.password}
          onChange={(e) => update({ password: e.target.value })}
          style={{ borderColor: errors.password ? 'var(--color-danger)' : undefined }}
        />
        {errors.password && (
          <p style={{ color: 'var(--color-danger)', fontSize: 'var(--text-xs)', marginTop: 4 }}>
            {errors.password}
          </p>
        )}
      </div>

      {/* Age + Gender row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <div>
          <label className="form-label">Age</label>
          <input
            className="form-input"
            type="number"
            min={1} max={120}
            placeholder="e.g. 34"
            value={form.age}
            onChange={(e) => update({ age: e.target.value })}
            style={{ borderColor: errors.age ? 'var(--color-danger)' : undefined }}
          />
          {errors.age && <p style={{ color: 'var(--color-danger)', fontSize: 'var(--text-xs)', marginTop: 4 }}>{errors.age}</p>}
        </div>
        <div>
          <label className="form-label">Gender</label>
          <select
            className="form-input form-select"
            value={form.gender}
            onChange={(e) => update({ gender: e.target.value })}
            style={{ borderColor: errors.gender ? 'var(--color-danger)' : undefined }}
          >
            <option value="">Select</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
          {errors.gender && <p style={{ color: 'var(--color-danger)', fontSize: 'var(--text-xs)', marginTop: 4 }}>{errors.gender}</p>}
        </div>
      </div>

      {/* City */}
      {field('City', 'city',
        loadingCities
          ? <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 0' }}>
              <Spinner size={16} /> <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>Loading cities…</span>
            </div>
          : <select
              className="form-input form-select"
              value={form.city}
              onChange={(e) => update({ city: e.target.value })}
              style={{ borderColor: errors.city ? 'var(--color-danger)' : undefined }}
            >
              <option value="">Select your city</option>
              {cities.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
      )}

      {/* Blood group — optional */}
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <label className="form-label">
          Blood group <span style={{ color: 'var(--color-text-muted)', fontWeight: 400, textTransform: 'none' }}>(optional)</span>
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {BLOOD_GROUPS.map((bg) => (
            <button
              key={bg}
              type="button"
              onClick={() => update({ blood_group: form.blood_group === bg ? '' : bg })}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--weight-medium)',
                border: `1.5px solid ${form.blood_group === bg ? 'var(--teal-500)' : 'var(--color-border)'}`,
                background: form.blood_group === bg ? 'var(--teal-50)' : '#fff',
                color: form.blood_group === bg ? 'var(--teal-700)' : 'var(--color-text-secondary)',
                transition: 'all var(--transition-fast)',
                cursor: 'pointer',
              }}
            >
              {bg}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button className="btn btn-navy btn-lg" onClick={handleNext}>
          Continue <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}
