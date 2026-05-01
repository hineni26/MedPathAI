import { IndianRupee, Shield, TrendingUp } from 'lucide-react'
import { formatINR } from '../../utils/formatCurrency'

const LABELS = {
  procedure: 'Procedure',
  doctor_fees: 'Doctor fees',
  hospital_stay: 'Hospital stay',
  diagnostics: 'Diagnostics',
  medicines: 'Medicines',
  contingency: 'Contingency',
}

export default function CostBreakdown({ cost }) {
  if (!cost) return null
  const entries = Object.entries(cost.breakdown || {})

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <IndianRupee size={16} color="var(--teal-600)" />
        <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>
          Estimated Cost
          {cost.selected_hospital?.hospital_name ? ` - ${cost.selected_hospital.hospital_name}` : ''}
        </h3>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 10,
        marginBottom: 14,
      }}>
        <Summary label="Total range" value={`${formatINR(cost.total_min)} - ${formatINR(cost.total_max)}`} />
        <Summary label="You may pay" value={`${formatINR(cost.you_pay_min)} - ${formatINR(cost.you_pay_max)}`} />
        <Summary label="Confidence" value={`${Math.round((cost.confidence || 0) * 100)}%`} />
      </div>

      {cost.insurance_covers > 0 && (
        <div style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          padding: '9px 12px',
          borderRadius: 'var(--radius-lg)',
          background: 'var(--green-50)',
          color: 'var(--green-600)',
          fontSize: 'var(--text-xs)',
          marginBottom: 12,
        }}>
          <Shield size={14} />
          Insurance cover applied: {formatINR(cost.insurance_covers)}
        </div>
      )}

      {entries.length > 0 && (
        <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          {entries.map(([key, val], index) => (
            <div
              key={key}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: 12,
                padding: '9px 12px',
                background: index % 2 ? 'var(--gray-50)' : '#fff',
                fontSize: 'var(--text-xs)',
              }}
            >
              <span style={{ color: 'var(--color-text-secondary)' }}>{LABELS[key] || key}</span>
              <strong>{formatINR(val.min)} - {formatINR(val.max)}</strong>
            </div>
          ))}
        </div>
      )}

      {cost.comorbidity_warnings?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {cost.comorbidity_warnings.map((warning) => (
            <div key={warning} style={{
              display: 'flex',
              gap: 7,
              alignItems: 'center',
              fontSize: 'var(--text-xs)',
              color: 'var(--amber-600)',
              marginTop: 5,
            }}>
              <TrendingUp size={13} />
              {warning}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Summary({ label, value }) {
  return (
    <div style={{ padding: 12, borderRadius: 'var(--radius-lg)', background: 'var(--gray-50)' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>{value}</div>
    </div>
  )
}
