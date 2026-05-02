import { formatINR } from '../../utils/formatCurrency'

// Map doc_type → which extracted fields to display and how to format them
const FIELD_CONFIGS = {
  salary_slip: [
    { key: 'monthly_income',    label: 'Monthly Income',    format: 'currency' },
    { key: 'employer_name',     label: 'Employer',          format: 'text' },
    { key: 'month',             label: 'Month',             format: 'text' },
  ],
  itr: [
    { key: 'annual_income',     label: 'Annual Income',     format: 'currency' },
    { key: 'tax_paid',          label: 'Tax Paid',          format: 'currency' },
    { key: 'assessment_year',   label: 'AY',                format: 'text' },
  ],
  balance_sheet: [
    { key: 'net_worth',         label: 'Net Worth',         format: 'currency' },
    { key: 'total_assets',      label: 'Total Assets',      format: 'currency' },
    { key: 'total_liabilities', label: 'Total Liabilities', format: 'currency' },
  ],
  cibil_report: [
    { key: 'cibil_score',       label: 'CIBIL Score',       format: 'score' },
    { key: 'active_loans',      label: 'Active Loans',      format: 'text' },
    { key: 'overdue_accounts',  label: 'Overdue Accounts',  format: 'text' },
  ],
  insurance_policy: [
    { key: 'sum_insured',       label: 'Sum Insured',       format: 'currency' },
    { key: 'provider',          label: 'Provider',          format: 'text' },
    { key: 'expiry_date',       label: 'Valid Until',       format: 'text' },
  ],
  medical_records: [
    { key: 'diagnosis',         label: 'Diagnosis',         format: 'text' },
    { key: 'doctor_name',       label: 'Doctor',            format: 'text' },
    { key: 'hospital',          label: 'Hospital',          format: 'text' },
  ],
}

function formatValue(value, format) {
  if (value === null || value === undefined || value === '') return '-'
  switch (format) {
    case 'currency': return formatINR(Number(value))
    case 'score':
      return (
        <span style={{
          fontWeight: 'var(--weight-semibold)',
          color: Number(value) >= 700
            ? 'var(--green-600)'
            : Number(value) >= 600
              ? 'var(--amber-600)'
              : 'var(--red-600)',
        }}>
          {value}
        </span>
      )
    default: return String(value)
  }
}

export default function ExtractionPreview({ data, docType }) {
  const fields = FIELD_CONFIGS[docType] || []
  const visible = fields.filter(({ key }) => data[key] !== undefined && data[key] !== null)

  if (!visible.length) return null

  return (
    <div style={{
      background: 'var(--color-bg-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
    }}>
      {visible.map(({ key, label, format }, i) => (
        <div
          key={key}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '7px 12px',
            borderBottom: i < visible.length - 1 ? '1px solid var(--color-border)' : 'none',
            background: i % 2 === 0 ? 'var(--color-bg-surface)' : 'var(--color-bg-muted)',
          }}
        >
          <span style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-muted)',
          }}>
            {label}
          </span>
          <span style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--weight-medium)',
            color: 'var(--color-text-primary)',
          }}>
            {formatValue(data[key], format)}
          </span>
        </div>
      ))}
    </div>
  )
}
