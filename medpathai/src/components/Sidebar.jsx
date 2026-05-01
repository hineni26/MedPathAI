import { NavLink, useNavigate } from 'react-router'
import { UserCircle, FileText, MessageCircle, Activity, LogOut, LogIn, Moon, Sun } from 'lucide-react'
import { useUserStore } from '../store/userStore'
import { clearUserId, clearRegistration, isRegistered } from '../api/auth'
import { useChatStore } from '../store/chatStore'
import { useUIStore } from '../store/uiStore'

const NAV = [
  { to: '/login',    icon: LogIn,         label: 'Login',     end: true  },
  { to: '/register', icon: UserCircle,    label: 'Profile',   end: true  },
  { to: '/documents',icon: FileText,      label: 'Documents', end: false },
  { to: '/chat',     icon: MessageCircle, label: 'Chat',      end: false },
]

export default function Sidebar() {
  const profile  = useUserStore((s) => s.profile)
  const clearUser = useUserStore((s) => s.clearUser)
  const navigate = useNavigate()
  const clearChat = useChatStore((s) => s.clearChat)
  const theme = useUIStore((s) => s.theme)
  const toggleTheme = useUIStore((s) => s.toggleTheme)
  const loggedIn = isRegistered()
  const isDark = theme === 'dark'

  function handleLogout() {
    clearUserId()
    clearRegistration()
    clearUser()
    clearChat()
    navigate('/login')
  }

  return (
    <aside className="app-sidebar">
      {/* Logo */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--teal-500)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Activity size={18} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 'var(--text-md)',
              color: '#fff',
              letterSpacing: '-0.01em',
            }}>
              MedPath AI
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'rgba(255,255,255,0.45)', marginTop: 1 }}>
              by Poonawalla Fincorp
            </div>
          </div>
        </div>
      </div>

      {/* User chip */}
      {profile && (
        <div style={{
          margin: '12px 12px 4px',
          padding: '10px 12px',
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 'var(--radius-lg)',
        }}>
          <div style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-medium)',
            color: '#fff',
          }}>
            {profile.name}
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
            {profile.city} · {profile.age}y
          </div>
        </div>
      )}

      {/* Nav */}
      <nav style={{ padding: '8px 12px', flex: 1 }}>
        {NAV.filter((item) => loggedIn || item.to === '/login' || item.to === '/register').map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 'var(--radius-lg)',
              marginBottom: 2,
              fontSize: 'var(--text-sm)',
              fontWeight: 'var(--weight-medium)',
              color: isActive ? '#fff' : 'rgba(255,255,255,0.55)',
              background: isActive ? 'rgba(23,176,167,0.18)' : 'transparent',
              textDecoration: 'none',
              transition: 'all var(--transition-fast)',
              borderLeft: isActive ? '2px solid var(--teal-500)' : '2px solid transparent',
            })}
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 12px 20px',
        borderTop: '1px solid rgba(255,255,255,0.08)',
      }}>
        <button
          onClick={toggleTheme}
          aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            width: '100%', padding: '10px 12px',
            borderRadius: 'var(--radius-lg)',
            color: 'rgba(255,255,255,0.72)',
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-medium)',
            transition: 'all var(--transition-fast)',
            cursor: 'pointer',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.08)',
            marginBottom: 8,
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = '#fff'
            e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = 'rgba(255,255,255,0.72)'
            e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
          }}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
          {isDark ? 'Light mode' : 'Dark mode'}
        </button>
        <button
          onClick={handleLogout}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            width: '100%', padding: '10px 12px',
            borderRadius: 'var(--radius-lg)',
            color: 'rgba(255,255,255,0.4)',
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-medium)',
            transition: 'all var(--transition-fast)',
            cursor: 'pointer', background: 'none', border: 'none',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
          onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.4)'}
        >
          <LogOut size={16} />
          Reset session
        </button>
      </div>
    </aside>
  )
}
