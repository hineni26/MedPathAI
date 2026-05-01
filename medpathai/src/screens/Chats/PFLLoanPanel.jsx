import { useState } from 'react'
import { Banknote, Send } from 'lucide-react'
import { Spinner } from '../../components/ui'
import { formatINR } from '../../utils/formatCurrency'
import useLoan from '../../hooks/useLoan'

export default function PFLLoanPanel({ options }) {
  const [tenure, setTenure] = useState(24)
  const { loading, submitLoan, result } = useLoan()

  if (!options?.loan_amount) return null

  const emiMap = {
    12: options.emi_12_months,
    24: options.emi_24_months,
    36: options.emi_36_months,
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Banknote size={17} color="var(--teal-600)" />
        <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>PFL Financing</h3>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 10,
        marginBottom: 12,
      }}>
        <Box label="Loan amount" value={formatINR(options.loan_amount)} />
        <Box label="Rate" value={options.interest_rate || '9.99% p.a.'} />
        <Box label={`${tenure} mo EMI`} value={formatINR(emiMap[tenure])} />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[12, 24, 36].map((months) => (
          <button
            key={months}
            type="button"
            className={`btn ${tenure === months ? 'btn-navy' : 'btn-outline'} btn-sm`}
            onClick={() => setTenure(months)}
          >
            {months} mo
          </button>
        ))}
      </div>

      {result?.pfl_contact && (
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--green-600)', marginBottom: 10 }}>
          {result.pfl_contact}
        </p>
      )}

      <button
        className="btn btn-primary"
        disabled={loading}
        onClick={() => submitLoan({ loanAmount: options.loan_amount, tenureMonths: tenure })}
        style={{ width: '100%' }}
      >
        {loading ? <><Spinner size={15} color="#fff" /> Sending...</> : <><Send size={15} /> Apply with Poonawalla Fincorp</>}
      </button>
    </div>
  )
}

function Box({ label, value }) {
  return (
    <div style={{ background: 'var(--gray-50)', borderRadius: 'var(--radius-lg)', padding: 10 }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>{value}</div>
    </div>
  )
}
