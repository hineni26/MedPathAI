import { Stethoscope } from 'lucide-react'

export default function PossibleCauses({ causes = [], icd10 }) {
  if (!causes.length && !icd10) return null

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <Stethoscope size={16} color="var(--teal-600)" />
        <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>Clinical Signals</h3>
      </div>
      {causes.length > 0 && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {causes.map((cause) => (
            <span key={cause} className="badge badge-metro">{cause}</span>
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
