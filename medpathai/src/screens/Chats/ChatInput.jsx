import { useState } from 'react'
import { LocateFixed, Send, X } from 'lucide-react'
import { Spinner } from '../../components/ui'

const EXAMPLES = [
  'I need a knee replacement in Mumbai under 3 lakh',
  'Chest pain and difficulty breathing',
  'Compare hospitals for cataract surgery in Pune',
]

export default function ChatInput({ onSend, disabled, location, onRequestLocation, locating }) {
  const [value, setValue] = useState('')

  async function submit(text = value) {
    const message = text.trim()
    if (!message || disabled) return
    setValue('')
    await onSend(message)
  }

  return (
    <div style={{
      borderTop: '1px solid var(--color-border)',
      background: 'var(--color-bg-surface)',
      padding: '14px 18px 18px',
    }}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => submit(example)}
            disabled={disabled}
            style={{
              border: '1px solid var(--color-border)',
              background: 'var(--gray-50)',
              whiteSpace: 'normal',
              textAlign: 'left',
            }}
          >
            {example}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
        style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}
      >
        <button
          type="button"
          className="btn btn-outline"
          onClick={onRequestLocation}
          disabled={disabled || locating}
          title="Use current location"
          style={{ width: 44, height: 44, padding: 0, flexShrink: 0 }}
        >
          {locating ? <Spinner size={16} /> : location ? <X size={16} /> : <LocateFixed size={16} />}
        </button>

        <textarea
          className="form-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Describe symptoms, procedure, budget, city, or urgency..."
          rows={1}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
          style={{
            minHeight: 44,
            maxHeight: 120,
            resize: 'vertical',
            lineHeight: 'var(--leading-snug)',
          }}
        />

        <button
          type="submit"
          className="btn btn-primary"
          disabled={disabled || !value.trim()}
          style={{ width: 48, height: 44, padding: 0, flexShrink: 0 }}
          title="Send message"
        >
          {disabled ? <Spinner size={16} color="#fff" /> : <Send size={17} />}
        </button>
      </form>
    </div>
  )
}
