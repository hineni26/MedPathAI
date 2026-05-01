import { useEffect, useRef } from 'react'
import { Activity } from 'lucide-react'
import { Spinner } from '../../components/ui'
import MessageBubble from './MessageBubble'
import EmergencyBanner from '../../components/EmergencyBanner'
import PossibleCauses from './PossibleCauses'
import HospitalCard from './HospitalCard'
import CostBreakdown from './CostBreakdown'
import EligibilityResult from './EligibilityResult'
import PFLLoanPanel from './PFLLoanPanel'
import ProviderModePanel from './ProviderModePanel'

export default function MessageList({ messages, loading, providerMode, selectedHospital, onSelectHospital }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  if (!messages.length) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 20px',
      }}>
        <div style={{ maxWidth: 520, textAlign: 'center' }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: 'var(--radius-2xl)',
            background: 'var(--teal-100)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 18px',
          }}>
            <Activity size={30} color="var(--teal-700)" />
          </div>
          <h2 style={{ fontSize: 'var(--text-xl)', marginBottom: 8 }}>Ask MedPath AI</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
            Describe a symptom, procedure, budget, deadline, or city. The assistant will find suitable hospitals, estimate costs, and show financing options.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
      {messages.map((message) => (
        <div key={message.id}>
          <MessageBubble message={message} />
          {message.role === 'ai' && message.data && (
            <ResultCards
              data={message.data}
              providerMode={providerMode}
              selectedHospital={selectedHospital}
              onSelectHospital={onSelectHospital}
            />
          )}
        </div>
      ))}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
          <Spinner size={16} /> Thinking through care options...
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}

function ResultCards({ data, providerMode, selectedHospital, onSelectHospital }) {
  if (data.type === 'clarification') {
    return (
      <div style={{ margin: '0 0 18px 40px', maxWidth: 720 }}>
        <PossibleCauses causes={data.possible_causes} />
      </div>
    )
  }

  const hospitals = data.hospitals || []

  return (
    <div style={{
      display: 'grid',
      gap: 12,
      margin: '0 0 20px 40px',
      maxWidth: 820,
    }}>
      {data.is_emergency && <EmergencyBanner hospitals={hospitals} />}
      <PossibleCauses causes={data.possible_causes} icd10={data.icd10_code} />
      {hospitals.length > 0 && (
        <div style={{ display: 'grid', gap: 10 }}>
          {hospitals.map((hospital) => (
            <HospitalCard
              key={hospital.hospital_id}
              hospital={hospital}
              selected={selectedHospital?.hospital_id === hospital.hospital_id}
              onSelect={onSelectHospital}
            />
          ))}
        </div>
      )}
      {providerMode && <ProviderModePanel hospitals={hospitals} />}
      <CostBreakdown cost={data.cost_result} />
      <EligibilityResult eligibility={data.loan_eligibility} />
      <PFLLoanPanel options={data.pfl_options} />
      {data.disclaimer && (
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', lineHeight: 'var(--leading-relaxed)' }}>
          {data.disclaimer}
        </p>
      )}
    </div>
  )
}
