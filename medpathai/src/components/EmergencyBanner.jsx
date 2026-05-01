import { Phone, AlertTriangle, MapPin } from 'lucide-react'

export default function EmergencyBanner({ hospitals = [] }) {
  const topHospital = hospitals[0]

  return (
    <div style={{
      background: 'var(--red-50)',
      border: '1.5px solid var(--red-500)',
      borderRadius: 'var(--radius-xl)',
      overflow: 'hidden',
      animation: 'fadeIn 0.3s ease both',
    }}>
      {/* Red top strip */}
      <div style={{
        background: 'var(--red-500)',
        padding: '10px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <AlertTriangle size={16} color="#fff" strokeWidth={2.5} />
        <span style={{
          color: '#fff',
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 'var(--text-sm)',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
        }}>
          Medical Emergency Detected
        </span>
      </div>

      <div style={{ padding: '16px 20px 20px' }}>
        <p style={{
          fontSize: 'var(--text-base)',
          fontWeight: 'var(--weight-medium)',
          color: 'var(--red-600)',
          marginBottom: 12,
          lineHeight: 'var(--leading-snug)',
        }}>
          This appears to be a time-critical situation. Please act immediately.
        </p>

        {/* Action row */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: topHospital ? 16 : 0 }}>
          <a
            href="tel:112"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              padding: '9px 18px',
              background: 'var(--red-500)',
              color: '#fff',
              borderRadius: 'var(--radius-lg)',
              fontWeight: 'var(--weight-medium)',
              fontSize: 'var(--text-sm)',
              textDecoration: 'none',
              transition: 'background var(--transition-fast)',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--red-600)'}
            onMouseLeave={e => e.currentTarget.style.background = 'var(--red-500)'}
          >
            <Phone size={14} strokeWidth={2.5} />
            Call 112 (Emergency)
          </a>

          <a
            href="tel:108"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              padding: '9px 18px',
              background: '#fff',
              color: 'var(--red-600)',
              border: '1.5px solid var(--red-100)',
              borderRadius: 'var(--radius-lg)',
              fontWeight: 'var(--weight-medium)',
              fontSize: 'var(--text-sm)',
              textDecoration: 'none',
              transition: 'all var(--transition-fast)',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--red-100)' }}
            onMouseLeave={e => { e.currentTarget.style.background = '#fff' }}
          >
            <Phone size={14} strokeWidth={2.5} />
            Call 108 (Ambulance)
          </a>
        </div>

        {/* Nearest hospital callout */}
        {topHospital && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
            padding: '12px 14px',
            background: '#fff',
            border: '1px solid var(--red-100)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <MapPin size={15} color="var(--red-500)" style={{ marginTop: 1, flexShrink: 0 }} />
            <div>
              <div style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--weight-medium)',
                color: 'var(--color-text-primary)',
              }}>
                Nearest recommended: {topHospital.hospital_name}
              </div>
              <div style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-secondary)',
                marginTop: 2,
              }}>
                {[
                  topHospital.emergency_24x7 && '24/7 Emergency',
                  topHospital.icu_beds && `${topHospital.icu_beds} ICU beds`,
                  (topHospital.ambulance_available || topHospital.ambulance) && 'Ambulance available',
                ].filter(Boolean).join(' · ')}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
