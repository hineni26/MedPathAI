import { Building2, Clock, IndianRupee, MapPin, ShieldCheck, Siren } from 'lucide-react'
import { Badge, RatingStars } from '../../components/ui'
import { formatINR } from '../../utils/formatCurrency'

export default function HospitalCard({ hospital, selected, onSelect }) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(hospital)}
      style={{
        width: '100%',
        textAlign: 'left',
        padding: 16,
        borderRadius: 'var(--radius-xl)',
        border: `1.5px solid ${selected ? 'var(--teal-500)' : 'var(--color-border)'}`,
        background: selected ? 'var(--teal-50)' : 'var(--color-bg-surface)',
        boxShadow: selected ? '0 0 0 3px rgba(23,176,167,0.12)' : 'var(--shadow-xs)',
        transition: 'all var(--transition-fast)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
            <Building2 size={16} color="var(--navy-600)" style={{ flexShrink: 0 }} />
            <h3 className="truncate" style={{ fontSize: 'var(--text-base)', fontWeight: 700 }}>
              {hospital.hospital_name}
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <RatingStars rating={hospital.rating || 0} />
            {hospital.nabh_accredited && <Badge variant="nabh">NABH</Badge>}
            {hospital.jci_accredited && <Badge variant="jci">JCI</Badge>}
            {hospital.over_budget && <Badge variant="yellow">Over budget</Badge>}
          </div>
        </div>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          color: 'var(--teal-700)',
          fontWeight: 700,
        }}>
          {Math.round(hospital.score || 0)}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 10,
        marginTop: 14,
      }}>
        <Metric
          icon={IndianRupee}
          label="Cost"
          value={`${formatINR(hospital.cost_min ?? hospital.cost_result?.total_min, true)} – ${formatINR(hospital.cost_max ?? hospital.cost_result?.total_max, true)}`}
          estimated={hospital.cost_result?.is_estimated}
          />
        <Metric
         icon={Clock}
         label="Wait"
         value={`${hospital.waiting_days ?? hospital.cost_result?.selected_hospital?.waiting_days ?? 'N/A'} days`}
         />
        <Metric icon={MapPin} label="Distance" value={hospital.distance_km ? `${hospital.distance_km} km` : hospital.city} />
        <Metric icon={ShieldCheck} label="Cashless" value={hospital.cashless_insurance ? 'Available' : 'Check first'} />
      </div>

      {hospital.emergency_24x7 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginTop: 12,
          color: 'var(--red-600)',
          fontSize: 'var(--text-xs)',
          fontWeight: 'var(--weight-medium)',
        }}>
          <Siren size={13} />
          24/7 emergency, {hospital.icu_beds || 0} ICU beds
        </div>
      )}
    </button>
  )
}

function Metric({ icon: Icon, label, value, estimated }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
      <Icon size={14} color="var(--color-text-muted)" style={{ flexShrink: 0 }} />
      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{label}</span>
          {estimated && (
            <span style={{
              fontSize: 10,
              fontWeight: 600,
              color: 'var(--teal-600)',
              background: 'var(--teal-50)',
              border: '1px solid var(--teal-200)',
              borderRadius: 4,
              padding: '0 4px',
              lineHeight: '14px',
            }}>
              AI est.
            </span>
          )}
        </div>
        <div className="truncate" style={{ fontSize: 'var(--text-xs)', fontWeight: 600 }}>{value}</div>
      </div>
    </div>
  )
}
