import { useRef, useState } from 'react'
import { FileText, CheckCircle, Clock, AlertCircle, Upload, Trash2, RefreshCw } from 'lucide-react'
import { DOC_TYPES } from '../../utils/staticData'
import ExtractionPreview from './ExtractionPreview'
import { deleteDocument, getDocuments, replaceDocument } from '../../api/documents'
import { useUserStore } from '../../store/userStore'
import { useUIStore } from '../../store/uiStore'

function statusMeta(status) {
  switch (status) {
    case 'done':
    case 'extracted':
      return { icon: CheckCircle, color: 'var(--green-500)', label: 'Extracted', bg: 'var(--green-50)', border: 'var(--green-100)' }
    case 'processing':
      return { icon: Clock, color: 'var(--amber-500)', label: 'Processing…', bg: 'var(--amber-50)', border: 'var(--amber-100)' }
    case 'pending':
    case 'uploaded':
    case 'manual_review':
      return { icon: Clock, color: 'var(--gray-500)', label: 'Uploaded', bg: 'var(--gray-50)', border: 'var(--gray-200)' }
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
  return <UploadedDocumentCard doc={doc} />
}

function UploadedDocumentCard({ doc }) {
  const userId = useUserStore((s) => s.userId)
  const setDocuments = useUserStore((s) => s.setDocuments)
  const toast = useUIStore((s) => s.toast)
  const replaceInputRef = useRef(null)
  const [replacing, setReplacing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const meta     = DOC_TYPES.find((d) => d.value === doc.doc_type)
  const status   = statusMeta(doc.extraction_status)
  const StatusIcon = status.icon

  async function refreshDocuments() {
    const docs = await getDocuments(userId)
    setDocuments(docs.documents || [])
  }

  async function handleReplace(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setReplacing(true)
    try {
      const result = await replaceDocument(userId, doc.id, file)
      await refreshDocuments()
      toast(result.message || 'Document replaced', 'success')
    } catch (err) {
      toast(err.message || 'Could not replace document', 'error')
    } finally {
      setReplacing(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('Delete this uploaded document?')) return

    setDeleting(true)
    try {
      await deleteDocument(userId, doc.id)
      await refreshDocuments()
      toast('Document deleted', 'success')
    } catch (err) {
      toast(err.message || 'Could not delete document', 'error')
    } finally {
      setDeleting(false)
    }
  }

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
          background: 'var(--color-bg-surface)',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 4,
            padding: '3px 8px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-bg-surface)',
            border: `1px solid ${status.border}`,
          }}>
            <StatusIcon size={11} color={status.color} />
            <span style={{ fontSize: 'var(--text-xs)', color: status.color, fontWeight: 'var(--weight-medium)' }}>
              {status.label}
            </span>
          </div>
        </div>
      </div>

      <input
        ref={replaceInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.webp"
        onChange={handleReplace}
        style={{ display: 'none' }}
      />

      {/* Extracted fields preview */}
      {['done', 'extracted'].includes(doc.extraction_status) && doc.extracted_data && (
        <ExtractionPreview data={doc.extracted_data} docType={doc.doc_type} />
      )}

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
        marginTop: 8,
      }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
          {new Date(doc.uploaded_at).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric',
          })}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            type="button"
            onClick={() => replaceInputRef.current?.click()}
            disabled={replacing || deleting}
            title="Replace file"
            style={{
              width: 30, height: 30, borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)', background: 'var(--color-bg-surface)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: replacing || deleting ? 'not-allowed' : 'pointer',
            }}
          >
            <RefreshCw size={13} color="var(--color-text-muted)" />
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={replacing || deleting}
            title="Delete document"
            style={{
              width: 30, height: 30, borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--red-100)', background: 'var(--red-50)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: replacing || deleting ? 'not-allowed' : 'pointer',
            }}
          >
            <Trash2 size={13} color="var(--red-500)" />
          </button>
        </div>
      </div>
    </div>
  )
}
