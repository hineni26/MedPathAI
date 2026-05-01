import { useEffect, useRef, useState } from 'react'
import { Activity, Banknote } from 'lucide-react'
import { Spinner } from '../../components/ui'
import MessageBubble from './MessageBubble'
import EmergencyBanner from '../../components/EmergencyBanner'
import HospitalCard from './HospitalCard'
import CostBreakdown from './CostBreakdown'
import EligibilityResult from './EligibilityResult'
import PFLLoanPanel from './PFLLoanPanel'
import ProviderModePanel from './ProviderModePanel'

export default function MessageList({ messages, loading, providerMode, profile, selectedHospital, onSelectHospital }) {
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
          <h2 style={{ fontSize: 'var(--text-xl)', marginBottom: 8 }}>
            Hi {profile?.name?.split(' ')[0] || 'there'}, I'm MedPath.
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
            Tell me what you're experiencing and I'll help you find the right care. What's going on?
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
  const [showFinancing, setShowFinancing] = useState(false)
  const selectedHospitalId = selectedHospital?.hospital_id

  useEffect(() => {
    setShowFinancing(false)
  }, [selectedHospitalId])

  if (data.type === 'clarification') {
    return null
  }

  const hospitals = data.hospitals || []
  const selectedInThisResult = hospitals.find(
    (hospital) => hospital.hospital_id === selectedHospitalId
  )
  const activeHospital = selectedInThisResult || null
  const activeHospitalId = activeHospital?.hospital_id
  const activeCost = data.cost_results_by_hospital?.[activeHospitalId] || activeHospital?.cost_result || data.cost_result
  const activePfl = data.pfl_options_by_hospital?.[activeHospitalId] || activeHospital?.pfl_options || data.pfl_options
  const activeEligibility = data.loan_eligibility_by_hospital?.[activeHospitalId] || activeHospital?.loan_eligibility || data.loan_eligibility

  return (
    <div style={{
      display: 'grid',
      gap: 12,
      margin: '0 0 20px 40px',
      maxWidth: 820,
    }}>
      {data.is_emergency && <EmergencyBanner hospitals={hospitals} />}
      {hospitals.length > 0 && (
        <div style={{ display: 'grid', gap: 10 }}>
          {hospitals.map((hospital) => (
            <HospitalCard
              key={hospital.hospital_id}
              hospital={hospital}
              selected={activeHospitalId === hospital.hospital_id}
              onSelect={onSelectHospital}
            />
          ))}
        </div>
      )}
      {providerMode && <ProviderModePanel hospitals={hospitals} />}
      {activeHospital && (
        <>
          <CostBreakdown cost={activeCost} />
          {!showFinancing ? (
            <div className="card" style={{
              padding: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                <Banknote size={17} color="var(--teal-600)" style={{ flexShrink: 0 }} />
                <div>
                  <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700 }}>
                    Want to check financing?
                  </h3>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                    I can show eligibility and EMI options for this hospital.
                  </p>
                </div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => setShowFinancing(true)}>
                Yes, check
              </button>
            </div>
          ) : (
            <>
              <EligibilityResult eligibility={activeEligibility} />
              <PFLLoanPanel options={activePfl} />
            </>
          )}
        </>
      )}
      {data.disclaimer && (
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', lineHeight: 'var(--leading-relaxed)' }}>
          {data.disclaimer}
        </p>
      )}
    </div>
  )
}
