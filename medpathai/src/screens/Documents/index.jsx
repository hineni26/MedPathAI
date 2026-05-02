import { Shield, Info } from 'lucide-react'
import { useUserStore } from '../../store/userStore'
import UploadDropzone from './UploadDropzone'
import DocumentCard from './DocumentCard'
import { Spinner } from '../../components/ui'
import useDocuments from '../../hooks/useDocuments'

const DOC_SECTIONS = {
  financial: {
    label: 'Financial Documents',
    hint: 'Required for PFL loan eligibility check',
    types: ['salary_slip', 'itr', 'balance_sheet'],
  },
  credit: {
    label: 'Credit & Liabilities',
    hint: 'Used to compute FOIR and max loan amount',
    types: ['cibil_report'],
  },
  medical: {
    label: 'Medical Records',
    hint: 'Helps AI pre-understand your condition',
    types: ['medical_records', 'insurance_policy'],
  },
}

export default function Documents() {
  const documents    = useUserStore((s) => s.documents)
  const { loading } = useDocuments()

  const docsByType = {}
  documents.forEach((d) => {
    docsByType[d.doc_type] = docsByType[d.doc_type] || []
    docsByType[d.doc_type].push(d)
  })

  return (
    <div className="app-content">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'var(--text-2xl)',
          fontWeight: 700,
          marginBottom: 6,
        }}>
          My Documents
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
          Pre-upload your financial and medical documents. Gemini reads and extracts
          key data so your loan eligibility check is instant during chat.
        </p>
      </div>

      {/* Privacy note */}
      <div style={{
        display: 'flex', gap: 10, alignItems: 'flex-start',
        padding: '12px 16px',
        background: 'var(--navy-50)',
        border: '1px solid var(--navy-100)',
        borderRadius: 'var(--radius-lg)',
        marginBottom: 'var(--space-8)',
      }}>
        <Shield size={15} color="var(--navy-500)" style={{ flexShrink: 0, marginTop: 2 }} />
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--navy-700)', lineHeight: 'var(--leading-relaxed)' }}>
          Documents are encrypted and stored securely. Only extracted data fields are used
          for loan eligibility — the raw files are never shared with third parties.
        </p>
      </div>

      {/* Upload dropzone */}
      <div className="card" style={{ marginBottom: 'var(--space-8)' }}>
        <h3 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'var(--text-md)',
          fontWeight: 600,
          marginBottom: 'var(--space-4)',
        }}>
          Upload a document
        </h3>
        <UploadDropzone />
      </div>

      {/* Document grid by section */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--color-text-secondary)' }}>
          <Spinner size={18} /> Loading your documents…
        </div>
      ) : (
        Object.entries(DOC_SECTIONS).map(([key, section]) => (
          <div key={key} style={{ marginBottom: 'var(--space-8)' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              marginBottom: 'var(--space-4)',
            }}>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-base)',
                fontWeight: 600,
              }}>
                {section.label}
              </h3>
              <span style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-muted)',
                display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <Info size={12} /> {section.hint}
              </span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: 12,
            }}>
              {section.types.map((type) => {
                const docs = docsByType[type] || []
                return docs.length > 0
                  ? docs.map((doc) => <DocumentCard key={doc.id} doc={doc} />)
                  : <DocumentCard key={type} doc={null} docType={type} />
              })}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
