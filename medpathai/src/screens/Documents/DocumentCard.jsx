import { FileText, CheckCircle, Clock, AlertCircle, Upload } from 'lucide-react'
import { DOC_TYPES } from '../../utils/staticData'
import ExtractionPreview from './ExtractionPreview'

function statusMeta(status) {
  switch (status) {
    case 'done':
    case 'extracted':
      return { icon: CheckCircle, color: 'var(--green-500)', label: 'Extracted', bg: 'var(--green-50)', border: 'var(--green-100)' }
    case 'pending':
    case 'processing':
      return { icon: Clock, color: 'var(--amber-500)', label: 'Processing…', bg: 'var(--amber-50)', border: 'var(--amber-100)' }
    case 'failed':
      return { icon: AlertCircle, color: 'var(--red-500)', label: 'Failed', bg: 'var(--red-50)', border: 'var(--red-100)' }
    default:
      return { icon: Clock, color: 'var(--gray-400)', label: 'Uploaded', bg: 'var(--gray-50)', border: 'var(--gray-200)' }
  }
}

// Empty slot — no document uploaded for this type yet
function EmptySlot({ docType }) {
  const meta = DOC_TYPES.find((d) => d.value === docType)
  return (
    <div style={{
      padding: '16px',
      borderRadius: 'var(--radius-xl)',
      border: '1.5px dashed var(--color-border)',
      background: 'var(--gray-50)',
      display: 'flex', alignItems: 'center', gap: 12,
      opacity: 0.7,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 'var(--radius-lg)',
        background: 'var(--gray-200)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Upload size={16} color="var(--gray-400)" />
      </div>
      <div>
        <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)', color: 'var(--color-text-secondary)' }}>
          {meta?.label || docType}
        </div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
          {meta?.hint || 'Not uploaded'}
        </div>
      </div>
    </div>
  )
}

export default function DocumentCard({ doc, docType }) {
  if (!doc) return <EmptySlot docType={docType} />

  const meta     = DOC_TYPES.find((d) => d.value === doc.doc_type)
  const status   = statusMeta(doc.extraction_status)
  const StatusIcon = status.icon

  return (
    <div style={{
      padding: 16,
      borderRadius: 'var(--radius-xl)',
      border: `1.5px solid ${status.border}`,
      background: status.bg,
      transition: 'box-shadow var(--transition-fast)',
    }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = 'var(--shadow-md)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--radius-lg)',
          background: '#fff',
          border: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <FileText size={17} color="var(--navy-500)" />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="truncate" style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-medium)',
            color: 'var(--color-text-primary)',
          }}>
            {meta?.label || doc.doc_type}
          </div>
          <div className="truncate" style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-muted)',
            marginTop: 1,
          }}>
            {doc.filename || doc.file_name}
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 4,
          padding: '3px 8px',
          borderRadius: 'var(--radius-full)',
          background: '#fff',
          border: `1px solid ${status.border}`,
          flexShrink: 0,
        }}>
          <StatusIcon size={11} color={status.color} />
          <span style={{ fontSize: 'var(--text-xs)', color: status.color, fontWeight: 'var(--weight-medium)' }}>
            {status.label}
          </span>
        </div>
      </div>

      {/* Extracted fields preview */}
      {['done', 'extracted'].includes(doc.extraction_status) && doc.extracted_data && (
        <ExtractionPreview data={doc.extracted_data} docType={doc.doc_type} />
      )}

      {/* Uploaded date */}
      <div style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--color-text-muted)',
        marginTop: 8,
      }}>
        {new Date(doc.uploaded_at).toLocaleDateString('en-IN', {
          day: 'numeric', month: 'short', year: 'numeric',
        })}
      </div>
    </div>
  )
}
