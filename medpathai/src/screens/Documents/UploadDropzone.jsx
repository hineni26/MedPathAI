import { useState, useRef } from 'react'
import { Upload, File, X } from 'lucide-react'
import { DOC_TYPES } from '../../utils/staticData'
import { getDocuments, uploadDocument } from '../../api/documents'
import { useUserStore } from '../../store/userStore'
import { useUIStore } from '../../store/uiStore'
import { Spinner } from '../../components/ui'

export default function UploadDropzone() {
  const userId     = useUserStore((s) => s.userId)
  const setDocuments = useUserStore((s) => s.setDocuments)
  const toast      = useUIStore((s) => s.toast)

  const [dragging, setDragging] = useState(false)
  const [file, setFile]         = useState(null)
  const [docType, setDocType]   = useState('')
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef()

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  function handleFile(e) {
    const picked = e.target.files[0]
    if (picked) setFile(picked)
  }

  async function handleUpload() {
    if (!file || !docType) return
    setUploading(true)
    setProgress(0)
    try {
      const result = await uploadDocument(userId, docType, file, setProgress)
      const docs = await getDocuments(userId)
      setDocuments(docs.documents || [])
      toast(result.message || `${file.name} uploaded successfully`, 'success')
      setFile(null)
      setDocType('')
      setProgress(0)
    } catch (err) {
      toast(err.message || 'Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  const canUpload = file && docType && !uploading

  return (
    <div>
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !file && inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--teal-500)' : file ? 'var(--teal-300)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-xl)',
          padding: '28px 20px',
          textAlign: 'center',
          cursor: file ? 'default' : 'pointer',
          background: dragging ? 'var(--teal-50)' : file ? 'var(--gray-50)' : '#fff',
          transition: 'all var(--transition-base)',
          marginBottom: 'var(--space-4)',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          style={{ display: 'none' }}
          onChange={handleFile}
        />

        {file ? (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: 'var(--radius-lg)',
              background: 'var(--teal-100)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <File size={18} color="var(--teal-700)" />
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>
                {file.name}
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                {(file.size / 1024).toFixed(0)} KB
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null) }}
              style={{
                marginLeft: 8, padding: 4, borderRadius: 'var(--radius-full)',
                background: 'var(--gray-200)', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center',
              }}
            >
              <X size={13} color="var(--gray-600)" />
            </button>
          </div>
        ) : (
          <>
            <div style={{
              width: 44, height: 44, borderRadius: 'var(--radius-xl)',
              background: 'var(--gray-100)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 12px',
            }}>
              <Upload size={20} color="var(--gray-400)" />
            </div>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
              <span style={{ color: 'var(--teal-600)', fontWeight: 'var(--weight-medium)' }}>
                Click to upload
              </span>{' '}or drag and drop
            </p>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              PDF, JPG or PNG · Max 10MB
            </p>
          </>
        )}
      </div>

      {/* Doc type selector + upload button */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label className="form-label">Document type</label>
          <select
            className="form-input form-select"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
          >
            <option value="">Select type…</option>
            {DOC_TYPES.map(({ value, label, hint }) => (
              <option key={value} value={value}>{label} — {hint}</option>
            ))}
          </select>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={!canUpload}
          style={{ flexShrink: 0, alignSelf: 'flex-end' }}
        >
          {uploading ? <><Spinner size={15} color="#fff" /> Uploading…</> : <><Upload size={15} /> Upload</>}
        </button>
      </div>

      {/* Progress bar */}
      {uploading && (
        <div style={{
          marginTop: 12,
          height: 4,
          background: 'var(--gray-100)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${progress}%`,
            background: 'var(--teal-500)',
            borderRadius: 'var(--radius-full)',
            transition: 'width 0.2s ease',
          }} />
        </div>
      )}
    </div>
  )
}
