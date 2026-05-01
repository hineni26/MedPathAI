import { Stethoscope } from 'lucide-react'

export default function PossibleCauses({ causes = [], icd10 }) {
  const signals = Array.from(new Set((causes || []).filter(Boolean))).slice(0, 4)

  if (!signals.length && !icd10) return null

  return (
    <div className="card" style={{
      padding: '18px 20px',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 9,
        marginBottom: signals.length ? 12 : 0,
      }}>
        <Stethoscope size={17} color="var(--teal-700)" />
        <h3 style={{
          fontSize: 'var(--text-base)',
          fontWeight: 700,
          letterSpacing: 0,
        }}>
          Clinical Signals
        </h3>
      </div>
      {signals.length > 0 && (
        <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap' }}>
          {signals.map((signal) => (
            <span
              key={signal}
              className="badge badge-metro"
              style={{
                border: '1px solid rgba(176, 200, 228, 0.35)',
                borderRadius: 'var(--radius-full)',
                padding: '6px 12px',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                letterSpacing: 0,
              }}
            >
              {signal}
            </span>
          ))}
        </div>
      )}
      {icd10 && (
        <p style={{ marginTop: 10, fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
          ICD-10 hint: <strong>{icd10}</strong>
        </p>
      )}
    </div>
  )
}
