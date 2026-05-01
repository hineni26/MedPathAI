import { useLocation } from 'react-router'
import { Building2 } from 'lucide-react'
import { useUIStore } from '../store/uiStore'

const PAGE_TITLES = {
  '/login':     'Login',
  '/register':  'Health Profile',
  '/documents': 'My Documents',
  '/chat':      'MedPath Chat',
}

export default function TopBar() {
  const location   = useLocation()
  const title      = PAGE_TITLES[location.pathname] || 'MedPath AI'
  const { providerMode, setProviderMode } = useUIStore()

  return (
    <header className="app-topbar" style={{ justifyContent: 'space-between' }}>
      <h1 style={{
        fontFamily: 'var(--font-display)',
        fontWeight: 600,
        fontSize: 'var(--text-md)',
        color: 'var(--color-text-primary)',
      }}>
        {title}
      </h1>

      {/* Provider mode toggle — only on chat */}
      {location.pathname === '/chat' && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: `1.5px solid ${providerMode ? 'var(--teal-300)' : 'var(--color-border)'}`,
          background: providerMode ? 'var(--teal-50)' : 'transparent',
          transition: 'all var(--transition-base)',
          cursor: 'pointer',
          userSelect: 'none',
        }}
          onClick={() => setProviderMode(!providerMode)}
        >
          <Building2
            size={15}
            color={providerMode ? 'var(--teal-600)' : 'var(--color-text-muted)'}
          />
          <span style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--weight-medium)',
            color: providerMode ? 'var(--teal-700)' : 'var(--color-text-secondary)',
          }}>
            Provider Mode
          </span>

          {/* Toggle switch */}
          <div style={{
            width: 28, height: 16,
            background: providerMode ? 'var(--teal-500)' : 'var(--gray-300)',
            borderRadius: 8,
            position: 'relative',
            transition: 'background var(--transition-base)',
          }}>
            <div style={{
              position: 'absolute',
              top: 2, left: providerMode ? 14 : 2,
              width: 12, height: 12,
              background: '#fff',
              borderRadius: '50%',
              transition: 'left var(--transition-spring)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
            }} />
          </div>
        </div>
      )}
    </header>
  )
}
