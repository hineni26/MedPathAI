import { ArrowLeft, ArrowRight, Info } from 'lucide-react'
import { COMORBIDITIES } from '../../utils/staticData'

export default function StepComorbidities({ form, update, onBack, onNext }) {
  function toggle(value) {
    const current = form.comorbidities
    const next = current.includes(value)
      ? current.filter((c) => c !== value)
      : [...current, value]
    update({ comorbidities: next })
  }

  return (
    <div>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-lg)',
        fontWeight: 600,
        marginBottom: 8,
      }}>
        Any existing conditions?
      </h3>
      <p style={{
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
        marginBottom: 'var(--space-6)',
        lineHeight: 'var(--leading-relaxed)',
      }}>
        This helps us apply accurate cost adjustments. Select all that apply, or skip if none.
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 10,
        marginBottom: 'var(--space-6)',
      }}>
        {COMORBIDITIES.map(({ value, label, multiplier }) => {
          const selected = form.comorbidities.includes(value)
          return (
            <button
              key={value}
              type="button"
              onClick={() => toggle(value)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: 'var(--radius-lg)',
                border: `1.5px solid ${selected ? 'var(--teal-400)' : 'var(--color-border)'}`,
                background: selected ? 'var(--teal-50)' : 'var(--color-bg-input)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all var(--transition-fast)',
              }}
            >
              <span style={{
                fontSize: 'var(--text-sm)',
                fontWeight: selected ? 'var(--weight-medium)' : 'var(--weight-regular)',
                color: selected ? 'var(--teal-800)' : 'var(--color-text-primary)',
              }}>
                {label}
              </span>
              {selected && (
                <span style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--teal-600)',
                  fontWeight: 'var(--weight-medium)',
                  background: 'var(--teal-100)',
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                  whiteSpace: 'nowrap',
                  marginLeft: 6,
                }}>
                  +{Math.round(multiplier * 100)}%
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Cost impact notice */}
      {form.comorbidities.length > 0 && (
        <div style={{
          display: 'flex',
          gap: 8,
          padding: '10px 14px',
          background: 'var(--amber-50)',
          border: '1px solid var(--amber-100)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-6)',
        }}>
          <Info size={15} color="var(--amber-600)" style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--amber-600)', lineHeight: 'var(--leading-relaxed)' }}>
            Your selected conditions may increase estimated treatment costs. These adjustments will be shown in the cost breakdown.
          </p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn btn-outline" onClick={onBack}>
          <ArrowLeft size={15} /> Back
        </button>
        <button className="btn btn-navy btn-lg" onClick={onNext}>
          {form.comorbidities.length === 0 ? 'Skip' : 'Continue'} <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}
