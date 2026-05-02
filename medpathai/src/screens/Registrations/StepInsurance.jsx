import { ArrowLeft, ArrowRight, Shield } from 'lucide-react'

const PROVIDERS = [
  'Star Health', 'HDFC ERGO', 'ICICI Lombard', 'Niva Bupa',
  'Bajaj Allianz', 'New India Assurance', 'United India', 'Oriental Insurance', 'Other',
]

export default function StepInsurance({ form, update, onBack, onNext }) {
  const hasInsurance = !!form.insurance_provider

  return (
    <div>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-lg)',
        fontWeight: 600,
        marginBottom: 8,
      }}>
        Health insurance
      </h3>
      <p style={{
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
        marginBottom: 'var(--space-6)',
        lineHeight: 'var(--leading-relaxed)',
      }}>
        We'll deduct your insurance coverage from the treatment cost estimate. Skip if you don't have insurance.
      </p>

      {/* Provider grid */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <label className="form-label">Insurance provider</label>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
          gap: 8,
          marginBottom: 8,
        }}>
          {PROVIDERS.map((p) => {
            const selected = form.insurance_provider === p
            return (
              <button
                key={p}
                type="button"
                onClick={() => update({ insurance_provider: selected ? '' : p })}
                style={{
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-lg)',
                  border: `1.5px solid ${selected ? 'var(--teal-400)' : 'var(--color-border)'}`,
                  background: selected ? 'var(--teal-50)' : 'var(--color-bg-input)',
                  fontSize: 'var(--text-sm)',
                  fontWeight: selected ? 'var(--weight-medium)' : 'var(--weight-regular)',
                  color: selected ? 'var(--teal-800)' : 'var(--color-text-primary)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  textAlign: 'left',
                }}
              >
                {p}
              </button>
            )
          })}
        </div>
      </div>

      {/* Coverage amount — only if provider selected */}
      {hasInsurance && (
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label className="form-label">Sum insured (₹)</label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--color-text-muted)',
              fontSize: 'var(--text-base)',
              fontWeight: 'var(--weight-medium)',
              pointerEvents: 'none',
            }}>₹</span>
            <input
              className="form-input"
              type="number"
              placeholder="e.g. 500000"
              value={form.insurance_coverage}
              onChange={(e) => update({ insurance_coverage: e.target.value })}
              style={{ paddingLeft: 28 }}
            />
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 4 }}>
            This is the maximum amount your insurer will cover
          </p>
        </div>
      )}

      {/* No insurance note */}
      {!hasInsurance && (
        <div style={{
          display: 'flex',
          gap: 8,
          padding: '10px 14px',
          background: 'var(--navy-50)',
          border: '1px solid var(--navy-100)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-6)',
        }}>
          <Shield size={15} color="var(--navy-500)" style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--navy-600)', lineHeight: 'var(--leading-relaxed)' }}>
            No insurance? MedPath will show the full out-of-pocket cost and Poonawalla Fincorp loan options to help you cover it.
          </p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn btn-outline" onClick={onBack}>
          <ArrowLeft size={15} /> Back
        </button>
        <button className="btn btn-navy btn-lg" onClick={onNext}>
          {!hasInsurance ? 'Skip' : 'Continue'} <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}
