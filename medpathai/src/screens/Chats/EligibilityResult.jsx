import { AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react'
import { EligibilityPill } from '../../components/ui'

export default function EligibilityResult({ eligibility }) {
  if (!eligibility) return null

  const Icon = eligibility.decision === 'GREEN'
    ? CheckCircle2
    : eligibility.decision === 'RED'
      ? AlertCircle
      : HelpCircle

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Icon size={16} color="var(--teal-600)" />
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>Loan Eligibility</h3>
        </div>
        <EligibilityPill decision={eligibility.decision || 'UNKNOWN'} />
      </div>

      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: 'var(--leading-relaxed)' }}>
        {eligibility.recommendation || 'Upload financial documents to get an instant eligibility check.'}
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
        gap: 8,
        marginTop: 12,
      }}>
        <Small label="Score" value={eligibility.score ?? 'N/A'} />
        <Small label="FOIR" value={eligibility.foir_pct || 'N/A'} />
        <Small label="EMI" value={eligibility.proposed_emi ? `Rs ${eligibility.proposed_emi.toLocaleString('en-IN')}` : 'N/A'} />
      </div>

      {eligibility.flags?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {eligibility.flags.map((flag) => (
            <p key={flag} style={{ fontSize: 'var(--text-xs)', color: 'var(--red-600)', marginTop: 4 }}>
              {flag}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function Small({ label, value }) {
  return (
    <div style={{ padding: 10, borderRadius: 'var(--radius-lg)', background: 'var(--gray-50)' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{label}</div>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>{value}</div>
    </div>
  )
}
