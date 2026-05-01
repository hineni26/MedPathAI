import { CheckCircle, MessageCircle, FileText } from 'lucide-react'
import { useNavigate } from 'react-router'

export default function StepDone({ name, onGo }) {
  const navigate = useNavigate()

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
      padding: 'var(--space-16) var(--space-8)',
    }}>
      <div style={{
        width: 72, height: 72,
        borderRadius: '50%',
        background: 'var(--green-100)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 'var(--space-6)',
      }}>
        <CheckCircle size={36} color="var(--green-600)" strokeWidth={1.5} />
      </div>

      <h2 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-2xl)',
        fontWeight: 700,
        marginBottom: 10,
      }}>
        You're all set{name ? `, ${name.split(' ')[0]}` : ''}!
      </h2>

      <p style={{
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-base)',
        maxWidth: 400,
        lineHeight: 'var(--leading-relaxed)',
        marginBottom: 'var(--space-10)',
      }}>
        Your health profile is saved. MedPath AI will use it to personalise every recommendation — no more repeated questions.
      </p>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
        <button className="btn btn-primary btn-lg" onClick={onGo}>
          <MessageCircle size={17} />
          Start chatting
        </button>
        <button
          className="btn btn-outline btn-lg"
          onClick={() => navigate('/documents')}
        >
          <FileText size={17} />
          Upload documents
        </button>
      </div>

      <p style={{
        marginTop: 'var(--space-6)',
        fontSize: 'var(--text-xs)',
        color: 'var(--color-text-muted)',
      }}>
        Upload salary slips, ITR & CIBIL report for instant loan eligibility checks
      </p>
    </div>
  )
}
