import { useCallback, useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Clock, FileText, Landmark, ReceiptText, Shield, TrendingUp, XCircle } from 'lucide-react'
import { getLoanApplications } from '../../api/loan'
import { useUserStore } from '../../store/userStore'
import { Spinner } from '../../components/ui'
import './style.css'

function fmtInr(value) {
  if (!value) return '-'
  return `Rs. ${Number(value).toLocaleString('en-IN')}`
}

function fmtDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function parseDocs(documentsJson) {
  try {
    const docs = JSON.parse(documentsJson || '[]')
    return Array.isArray(docs) ? docs : []
  } catch {
    return []
  }
}

function docIcon(docType) {
  const icons = {
    salary_slip: Landmark,
    itr: FileText,
    bank_statement: Landmark,
    insurance_policy: Shield,
    cibil_report: TrendingUp,
    balance_sheet: FileText,
    pan: FileText,
  }
  return icons[docType] || FileText
}

function statusMeta(status) {
  switch (status) {
    case 'APPROVED':
      return { icon: CheckCircle2, label: 'Accepted', tone: 'approved' }
    case 'REJECTED':
      return { icon: XCircle, label: 'Rejected', tone: 'rejected' }
    default:
      return { icon: Clock, label: 'Pending', tone: 'pending' }
  }
}

function Stat({ value, label, tone = '' }) {
  return (
    <div className="loan-history-stat">
      <div className={`loan-history-stat-num ${tone}`}>{value}</div>
      <div className="loan-history-stat-label">{label}</div>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="loan-history-info">
      <label>{label}</label>
      <span>{value}</span>
    </div>
  )
}

function LoanCard({ loan }) {
  const status = statusMeta(loan.status)
  const StatusIcon = status.icon
  const docs = parseDocs(loan.documents_json)
  const foirPct = loan.foir ? `${Math.round(loan.foir * 100)}%` : '-'

  return (
    <article className={`loan-history-card ${status.tone}`}>
      <div className="loan-history-card-header">
        <div>
          <div className="loan-history-ref">{loan.reference_id}</div>
          <div className="loan-history-time">Applied {fmtDate(loan.applied_at)}</div>
        </div>
        <div className={`loan-history-status ${status.tone}`}>
          <StatusIcon size={14} />
          {status.label}
        </div>
      </div>

      <div className="loan-history-grid">
        <Info label="Hospital" value={loan.hospital_name || '-'} />
        <Info label="Procedure" value={loan.procedure || '-'} />
        <Info label="Loan Amount" value={fmtInr(loan.loan_amount)} />
        <Info label="EMI / Tenure" value={`${fmtInr(loan.emi)} x ${loan.tenure_months || '-'} mo`} />
        <Info label="Interest Rate" value={loan.interest_rate ? `${loan.interest_rate}%` : '-'} />
        <Info label="Processing Fee" value={fmtInr(loan.processing_fee)} />
        <Info label="FOIR" value={foirPct} />
        <Info label="Risk Band" value={loan.risk_band || '-'} />
      </div>

      {loan.officer_note && (
        <div className="loan-history-note">
          <strong>PFL note:</strong> {loan.officer_note}
        </div>
      )}

      {loan.decided_at && (
        <div className="loan-history-decided">
          Decision updated {fmtDate(loan.decided_at)}
        </div>
      )}

      <div className="loan-history-docs">
        <label>Attached Documents</label>
        <div className="loan-history-doc-list">
          {docs.length ? docs.map((doc, index) => {
            const Icon = docIcon(doc.doc_type)
            const docLabel = (doc.doc_type || 'document').replace(/_/g, ' ')

            if (!doc.url) {
              return (
                <span className="loan-history-doc-muted" key={`${doc.doc_type}-${index}`}>
                  <Icon size={14} /> {docLabel} (no URL)
                </span>
              )
            }

            return (
              <a className="loan-history-doc-link" href={doc.url} target="_blank" rel="noreferrer" key={`${doc.url}-${index}`}>
                <Icon size={14} />
                {docLabel}
              </a>
            )
          }) : <span className="loan-history-doc-muted">No documents attached</span>}
        </div>
      </div>
    </article>
  )
}

export default function LoanHistory() {
  const userId = useUserStore((s) => s.userId)
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const stats = useMemo(() => ({
    total: applications.length,
    pending: applications.filter((loan) => loan.status === 'PENDING').length,
    approved: applications.filter((loan) => loan.status === 'APPROVED').length,
    rejected: applications.filter((loan) => loan.status === 'REJECTED').length,
  }), [applications])

  const loadApplications = useCallback(async () => {
    try {
      setError('')
      const data = await getLoanApplications(userId)
      setApplications(data.applications || [])
    } catch (err) {
      setError(err.message || 'Could not load your loan history')
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    loadApplications()
  }, [loadApplications])

  return (
    <div className="app-content">
      <div className="loan-history-header">
        <div>
          <h2>My Loan History</h2>
          <p>Track previous PFL medical loan applications and their latest review status.</p>
        </div>
      </div>

      <section className="loan-history-stats">
        <Stat value={stats.total} label="Total" />
        <Stat value={stats.pending} label="Pending" tone="pending" />
        <Stat value={stats.approved} label="Approved" tone="approved" />
        <Stat value={stats.rejected} label="Rejected" tone="rejected" />
      </section>

      {loading ? (
        <div className="loan-history-loading">
          <Spinner size={18} /> Loading your loan records...
        </div>
      ) : error ? (
        <div className="loan-history-empty">
          <ReceiptText size={26} />
          <h3>Could not load loan records</h3>
          <p>{error}</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="loan-history-empty">
          <ReceiptText size={26} />
          <h3>No loan applications yet</h3>
          <p>Your submitted PFL medical loan applications will appear here.</p>
        </div>
      ) : (
        <main className="loan-history-list">
          {applications.map((loan) => (
            <LoanCard key={loan.reference_id} loan={loan} />
          ))}
        </main>
      )}
    </div>
  )
}
