import { ArrowLeft, ArrowRight, Info } from 'lucide-react'
import { EMPLOYMENT_TYPES } from '../../utils/staticData'

export default function StepFinancials({ form, update, onBack, onNext }) {
  return (
    <div>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-lg)',
        fontWeight: 600,
        marginBottom: 8,
      }}>
        Financial details
      </h3>
      <p style={{
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
        marginBottom: 'var(--space-6)',
        lineHeight: 'var(--leading-relaxed)',
      }}>
        Used only to estimate PFL loan eligibility. You can upload documents later for a precise check.
      </p>

      {/* Employment type */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <label className="form-label">Employment type</label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {EMPLOYMENT_TYPES.map(({ value, label }) => {
            const sel = form.employment_type === value
            return (
              <button
                key={value}
                type="button"
                onClick={() => update({ employment_type: value })}
                style={{
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-full)',
                  border: `1.5px solid ${sel ? 'var(--teal-400)' : 'var(--color-border)'}`,
                  background: sel ? 'var(--teal-50)' : '#fff',
                  fontSize: 'var(--text-sm)',
                  fontWeight: sel ? 'var(--weight-medium)' : 'var(--weight-regular)',
                  color: sel ? 'var(--teal-800)' : 'var(--color-text-primary)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Monthly income + existing EMI */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <div>
          <label className="form-label">Monthly income (₹)</label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--color-text-muted)', pointerEvents: 'none',
            }}>₹</span>
            <input
              className="form-input"
              type="number"
              placeholder="e.g. 75000"
              value={form.monthly_income}
              onChange={(e) => update({ monthly_income: e.target.value })}
              style={{ paddingLeft: 28 }}
            />
          </div>
        </div>
        <div>
          <label className="form-label">Existing EMIs (₹ / mo)</label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--color-text-muted)', pointerEvents: 'none',
            }}>₹</span>
            <input
              className="form-input"
              type="number"
              placeholder="0 if none"
              value={form.existing_emi}
              onChange={(e) => update({ existing_emi: e.target.value })}
              style={{ paddingLeft: 28 }}
            />
          </div>
        </div>
      </div>

      {/* CIBIL + years employed */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <div>
          <label className="form-label">CIBIL score</label>
          <input
            className="form-input"
            type="number"
            min={300} max={900}
            placeholder="e.g. 750"
            value={form.cibil_score}
            onChange={(e) => update({ cibil_score: e.target.value })}
          />
          {form.cibil_score && (
            <p style={{
              fontSize: 'var(--text-xs)',
              marginTop: 4,
              color: Number(form.cibil_score) >= 700
                ? 'var(--green-600)'
                : Number(form.cibil_score) >= 600
                  ? 'var(--amber-600)'
                  : 'var(--red-600)',
            }}>
              {Number(form.cibil_score) >= 700
                ? '✓ Good — eligible for PFL loans'
                : Number(form.cibil_score) >= 600
                  ? '~ Borderline — may need verification'
                  : '✕ Below PFL threshold (700)'}
            </p>
          )}
        </div>
        <div>
          <label className="form-label">Years employed</label>
          <input
            className="form-input"
            type="number"
            min={0}
            placeholder="e.g. 3"
            value={form.employment_years}
            onChange={(e) => update({ employment_years: e.target.value })}
          />
        </div>
      </div>

      {/* FOIR preview */}
      {form.monthly_income && form.existing_emi !== undefined && (
        <div style={{
          display: 'flex', gap: 8,
          padding: '10px 14px',
          background: 'var(--navy-50)',
          border: '1px solid var(--navy-100)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-6)',
        }}>
          <Info size={15} color="var(--navy-500)" style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--navy-600)', lineHeight: 'var(--leading-relaxed)' }}>
            Current FOIR: {Math.round((Number(form.existing_emi) / Number(form.monthly_income)) * 100) || 0}%
            &nbsp;· PFL limit is 50%. The remainder is your headroom for a medical loan EMI.
          </p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn btn-outline" onClick={onBack}>
          <ArrowLeft size={15} /> Back
        </button>
        <button className="btn btn-navy btn-lg" onClick={onNext}>
          Continue <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}
