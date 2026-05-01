import { BarChart3, Clock, IndianRupee, ShieldCheck } from 'lucide-react'
import { formatINR } from '../../utils/formatCurrency'

export default function ProviderModePanel({ hospitals = [] }) {
  if (!hospitals.length) return null

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <BarChart3 size={16} color="var(--navy-600)" />
        <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>Provider Comparison</h3>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
          <thead>
            <tr>
              {['Hospital', 'Score', 'Cost', 'Wait', 'Accreditation'].map((h) => (
                <th key={h} style={{
                  textAlign: 'left',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--color-text-muted)',
                  fontWeight: 600,
                  padding: '8px 10px',
                  borderBottom: '1px solid var(--color-border)',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {hospitals.map((h) => (
              <tr key={h.hospital_id}>
                <td style={cellStyle}>
                  <strong>{h.hospital_name}</strong>
                  <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>{h.city}</div>
                </td>
                <td style={cellStyle}>{Math.round(h.score || 0)}</td>
                <td style={cellStyle}><Inline icon={IndianRupee} text={`${formatINR(h.cost_min, true)} - ${formatINR(h.cost_max, true)}`} /></td>
                <td style={cellStyle}><Inline icon={Clock} text={`${h.waiting_days ?? 'N/A'} days`} /></td>
                <td style={cellStyle}><Inline icon={ShieldCheck} text={[h.nabh_accredited && 'NABH', h.jci_accredited && 'JCI'].filter(Boolean).join(', ') || 'Standard'} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const cellStyle = {
  padding: '10px',
  borderBottom: '1px solid var(--color-border)',
  fontSize: 'var(--text-xs)',
  verticalAlign: 'top',
}

function Inline({ icon: Icon, text }) {
  return (
    <span style={{ display: 'inline-flex', gap: 5, alignItems: 'center' }}>
      <Icon size={12} color="var(--color-text-muted)" />
      {text}
    </span>
  )
}
