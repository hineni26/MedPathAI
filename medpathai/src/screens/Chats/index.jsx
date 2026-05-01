import { RotateCcw } from 'lucide-react'
import ChatInput from './ChatInput'
import MessageList from './MessageList'
import useChat from '../../hooks/useChat'
import useGeolocation from '../../hooks/useGeolocation'
import useProfile from '../../hooks/useProfile'
import { useUIStore } from '../../store/uiStore'

export default function Chat() {
  const {
    messages,
    isLoading,
    selectedHospital,
    submitMessage,
    setSelectedHospital,
    clearChat,
  } = useChat()
  const { position, loading: locating, requestLocation } = useGeolocation()
  const { profile } = useProfile({ autoLoad: !messages.length })
  const providerMode = useUIStore((s) => s.providerMode)
  const toast = useUIStore((s) => s.toast)

  async function handleSend(message) {
    await submitMessage(message, position)
  }

  async function handleRequestLocation() {
    const loc = await requestLocation()
    if (loc) toast('Location enabled for distance estimates', 'success')
  }

  function handleSelectHospital(hospital) {
    setSelectedHospital(hospital)
    toast(`${hospital.hospital_name} selected`, 'success')
  }

  return (
    <div className="app-content" style={{
      maxWidth: 1120,
      display: 'flex',
      flexDirection: 'column',
      minHeight: 'calc(100vh - var(--topbar-height))',
      paddingBottom: 0,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 16,
        marginBottom: 16,
      }}>
        <div>
          <h2 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, marginBottom: 6 }}>
            Care navigation{profile?.name ? ` for ${profile.name.split(' ')[0]}` : ''}
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
            Hospital discovery, cost clarity, emergency support, and PFL financing in one guided chat.
          </p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={clearChat} disabled={isLoading}>
          <RotateCcw size={14} /> New chat
        </button>
      </div>

      <div className="card" style={{
        flex: 1,
        minHeight: 560,
        padding: 0,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <MessageList
          messages={messages}
          loading={isLoading}
          providerMode={providerMode}
          profile={profile}
          selectedHospital={selectedHospital}
          onSelectHospital={handleSelectHospital}
        />
        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          location={position}
          locating={locating}
          onRequestLocation={handleRequestLocation}
        />
      </div>
    </div>
  )
}
