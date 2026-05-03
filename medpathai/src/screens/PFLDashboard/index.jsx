import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Check, Clock, FileText, Landmark, Shield, TrendingUp, X } from 'lucide-react'
import { decidePFLApplication, getPFLApplications } from '../../api/pfl'
import { useUIStore } from '../../store/uiStore'
import './style.css'

const REFRESH_MS = 3000

function fmtInr(n) {
  if (!n) return '-'
  return `Rs. ${Number(n).toLocaleString('en-IN')}`
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

function parseDocs(documentsJson) {
  try {
    const docs = JSON.parse(documentsJson || '[]')
    return Array.isArray(docs) ? docs : []
  } catch {
    return []
  }
}

function Stat({ value, label, tone = '' }) {
  return (
    <div className="pfl-stat">
      <div className={`pfl-stat-num ${tone}`}>{value}</div>
      <div className="pfl-stat-label">{label}</div>
    </div>
  )
}

function EmptyState({ mode }) {
  const isError = mode === 'error'

  return (
    <div className="pfl-empty">
      <div className="pfl-empty-icon">{isError ? '!' : '-'}</div>
      <h3>{isError ? 'Cannot connect to MedPath backend' : 'No applications yet'}</h3>
      <p>
        {isError
          ? 'Make sure the server is running at the configured API URL.'
          : 'When a patient applies for a PFL loan on MedPath, it will appear here.'}
      </p>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="pfl-info-item">
      <label>{label}</label>
      <span>{value}</span>
    </div>
  )
}

function ApplicationCard({ app, note, onNoteChange, onDecide }) {
  const isPending = app.status === 'PENDING'
  const docs = parseDocs(app.documents_json)
  const riskClass = app.medpath_decision || 'YELLOW'
  const foirPct = app.foir ? `${Math.round(app.foir * 100)}%` : '-'

  return (
    <article className={`pfl-card ${app.status || ''}`}>
      <div className="pfl-card-header">
        <div>
          <div className="pfl-ref-id">{app.reference_id}</div>
          <div className="pfl-app-time">Applied {fmtDate(app.applied_at)}</div>
        </div>
        <span className={`pfl-status-badge badge-${app.status}`}>{app.status}</span>
      </div>

      <div className="pfl-card-body">
        <div className="pfl-info-grid">
          <Info label="Applicant" value={`${app.applicant_name || '-'}, ${app.age || '-'} yrs`} />
          <Info label="City" value={app.city || '-'} />
          <Info label="Hospital" value={app.hospital_name || '-'} />
          <Info label="Procedure" value={app.procedure || '-'} />
          <Info label="Loan Amount" value={fmtInr(app.loan_amount)} />
          <Info label="EMI / Tenure" value={`${fmtInr(app.emi)} x ${app.tenure_months || '-'} mo`} />
          <Info label="Monthly Income" value={fmtInr(app.monthly_income)} />
          <Info label="Existing EMI" value={fmtInr(app.existing_emi)} />
          <Info label="CIBIL Score" value={app.cibil_score || '-'} />
        </div>

        <div className="pfl-risk-row">
          <span className="pfl-risk-label">MedPath pre-check:</span>
          <span className={`pfl-risk-${riskClass}`}>{riskClass}</span>
          <span className="pfl-risk-label">FOIR: {foirPct}</span>
          <span className="pfl-risk-label">Risk band: {app.risk_band || '-'}</span>
        </div>

        <div className="pfl-docs-section">
          <label>Documents</label>
          <div className="pfl-doc-list">
            {docs.length ? docs.map((doc, index) => {
              const Icon = docIcon(doc.doc_type)
              const docLabel = (doc.doc_type || 'document').replace(/_/g, ' ')

              if (!doc.url) {
                return (
                  <span className="pfl-no-docs" key={`${doc.doc_type}-${index}`}>
                    <Icon size={14} /> {docLabel} (no URL)
                  </span>
                )
              }

              return (
                <a className="pfl-doc-link" href={doc.url} target="_blank" rel="noreferrer" key={`${doc.url}-${index}`}>
                  <Icon size={14} />
                  {docLabel}
                </a>
              )
            }) : <span className="pfl-no-docs">No documents attached</span>}
          </div>
        </div>

        {isPending ? (
          <div className="pfl-actions">
            <input
              className="pfl-note-input"
              value={note || ''}
              onChange={(event) => onNoteChange(app.reference_id, event.target.value)}
              placeholder="Optional officer note..."
            />
            <button className="pfl-btn-approve" onClick={() => onDecide(app.reference_id, 'APPROVED')}>
              <Check size={16} /> Approve
            </button>
            <button className="pfl-btn-reject" onClick={() => onDecide(app.reference_id, 'REJECTED')}>
              <X size={16} /> Reject
            </button>
          </div>
        ) : (
          <div className="pfl-decided-info">
            <strong>{app.status}</strong> on {fmtDate(app.decided_at)}
            {app.officer_note ? ` - "${app.officer_note}"` : ''}
          </div>
        )}
      </div>
    </article>
  )
}

export default function PFLDashboard() {
  const toast = useUIStore((s) => s.toast)
  const loadingRef = useRef(false)
  const [applications, setApplications] = useState([])
  const [notes, setNotes] = useState({})
  const [lastRefresh, setLastRefresh] = useState('Connecting...')
  const [hasConnectionError, setHasConnectionError] = useState(false)

  const stats = useMemo(() => ({
    total: applications.length,
    pending: applications.filter((a) => a.status === 'PENDING').length,
    approved: applications.filter((a) => a.status === 'APPROVED').length,
    rejected: applications.filter((a) => a.status === 'REJECTED').length,
  }), [applications])

  const loadApplications = useCallback(async () => {
    if (loadingRef.current) return
    loadingRef.current = true
    try {
      const data = await getPFLApplications()
      setApplications(data.applications || [])
      setHasConnectionError(false)
      setLastRefresh(`Last updated: ${new Date().toLocaleTimeString('en-IN')}`)
    } catch {
      setHasConnectionError(true)
      setLastRefresh('Cannot reach backend')
    } finally {
      loadingRef.current = false
    }
  }, [])

  useEffect(() => {
    const timeoutId = window.setTimeout(loadApplications, 0)
    const intervalId = window.setInterval(() => {
      if (!document.hidden) {
        loadApplications()
      }
    }, REFRESH_MS)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadApplications()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      window.clearTimeout(timeoutId)
      window.clearInterval(intervalId)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [loadApplications])

  function handleNoteChange(referenceId, note) {
    setNotes((current) => ({ ...current, [referenceId]: note }))
  }

  async function handleDecide(referenceId, decision) {
    try {
      const data = await decidePFLApplication(referenceId, decision, notes[referenceId]?.trim() || '')

      if (data.success) {
        toast(
          decision === 'APPROVED' ? `${referenceId} approved` : `${referenceId} rejected`,
          decision === 'APPROVED' ? 'success' : 'error',
          2800
        )
        setNotes((current) => ({ ...current, [referenceId]: '' }))
        loadApplications()
        return
      }

      toast('Something went wrong - try again', 'error', 2800)
    } catch {
      toast('Cannot reach backend - is it running?', 'error', 2800)
    }
  }

  return (
    <div className="pfl-page">
      <section className="pfl-header">
        <div className="pfl-header-left">
          <div className="pfl-header-logo">PF</div>
          <div>
            <h1>Poonawalla Fincorp</h1>
            <p>Loan Officer Dashboard - MedPath Applications</p>
          </div>
        </div>
        <div className="pfl-live-badge">
          <span className="pfl-live-dot" />
          Live - auto-refreshing
        </div>
      </section>

      <section className="pfl-stats-bar">
        <Stat value={stats.total} label="Total" />
        <Stat value={stats.pending} label="Pending" tone="yellow" />
        <Stat value={stats.approved} label="Approved" tone="green" />
        <Stat value={stats.rejected} label="Rejected" tone="red" />
      </section>

      <main className="pfl-main">
        <div className="pfl-refresh-row">
          <div className="pfl-section-title">Loan Applications</div>
          <div className="pfl-refresh-text">
            <Clock size={13} />
            {lastRefresh}
          </div>
        </div>

        {hasConnectionError ? (
          <EmptyState mode="error" />
        ) : applications.length === 0 ? (
          <EmptyState />
        ) : applications.map((app) => (
          <ApplicationCard
            key={app.reference_id}
            app={app}
            note={notes[app.reference_id]}
            onNoteChange={handleNoteChange}
            onDecide={handleDecide}
          />
        ))}
      </main>
    </div>
  )
}
