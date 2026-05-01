import { Bot, User } from 'lucide-react'

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      gap: 10,
      marginBottom: 14,
    }}>
      {!isUser && (
        <div style={{
          width: 30,
          height: 30,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--teal-100)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Bot size={16} color="var(--teal-700)" />
        </div>
      )}

      <div style={{
        maxWidth: 'min(680px, 82%)',
        padding: '12px 14px',
        borderRadius: isUser
          ? 'var(--radius-xl) var(--radius-xl) var(--radius-sm) var(--radius-xl)'
          : 'var(--radius-xl) var(--radius-xl) var(--radius-xl) var(--radius-sm)',
        background: isUser ? 'var(--navy-900)' : 'var(--color-bg-surface)',
        color: isUser ? '#fff' : 'var(--color-text-primary)',
        border: isUser ? '1px solid var(--navy-900)' : '1px solid var(--color-border)',
        boxShadow: isUser ? 'none' : 'var(--shadow-xs)',
        whiteSpace: 'pre-wrap',
        lineHeight: 'var(--leading-relaxed)',
        fontSize: 'var(--text-sm)',
      }}>
        {message.content}
      </div>

      {isUser && (
        <div style={{
          width: 30,
          height: 30,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--navy-100)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <User size={15} color="var(--navy-700)" />
        </div>
      )}
    </div>
  )
}
