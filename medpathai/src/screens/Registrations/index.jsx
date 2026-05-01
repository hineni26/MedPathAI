import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router'
import StepIndicator from '../../components/StepIndicator'
import StepHealthProfile from './StepHealthProfile'
import StepComorbidities from './StepComorbidities'
import StepInsurance from './StepInsurance'
import StepFinancials from './StepFinancials'
import StepEmergencyContact from './StepEmergencyContact'
import StepDone from './StepDone'
import { registerUser, getProfile } from '../../api/registration'
import { saveFinancials } from '../../api/financials'
import { useUserStore } from '../../store/userStore'
import { useUIStore } from '../../store/uiStore'
import { getUserId, markRegistered, isRegistered, setUserId as persistUserId } from '../../api/auth'

const STEPS = [
  { label: 'Profile' },
  { label: 'Conditions' },
  { label: 'Insurance' },
  { label: 'Financials' },
  { label: 'Emergency' },
]

const EMPTY_FORM = {
  // Step 1
  name: '', email: '', password: '', age: '', gender: '', city: '', blood_group: '',
  // Step 2
  comorbidities: [],
  // Step 3
  insurance_provider: '', insurance_coverage: '',
  // Step 4
  employment_type: '', monthly_income: '', existing_emi: '0',
  cibil_score: '', employment_years: '',
  // Step 5
  emergency_contact_name: '', emergency_contact_phone: '',
}

export default function Registration() {
  const navigate   = useNavigate()
  const userId     = getUserId()
  const setProfile    = useUserStore((s) => s.setProfile)
  const setStoreUserId = useUserStore((s) => s.setUserId)
  const setFinancials = useUserStore((s) => s.setFinancials)
  const toast      = useUIStore((s) => s.toast)

  const [step, setStep]       = useState(0)
  const [form, setForm]       = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(false)
  const [done, setDone]       = useState(false)

  // If already registered, pre-fill form from existing profile
  useEffect(() => {
    if (isRegistered()) {
      getProfile(userId)
        .then(({ profile, financials }) => {
          if (profile) {
            setForm((f) => ({ ...f, ...profile,
              monthly_income: financials?.monthly_income || '',
              existing_emi:   financials?.existing_emi   || '0',
              cibil_score:    financials?.cibil_score    || '',
              employment_type:financials?.employment_type|| '',
              employment_years:financials?.employment_years || '',
            }))
            setProfile(profile)
            if (financials) setFinancials(financials)
          }
        })
        .catch(() => {})
    }
  }, [setFinancials, setProfile, userId])

  function update(fields) {
    setForm((f) => ({ ...f, ...fields }))
  }

  async function handleFinish() {
    setLoading(true)
    try {
      // 1 — save health profile
      const registerResult = await registerUser({
        user_id:                 userId,
        email:                   form.email.trim().toLowerCase(),
        password:                form.password || undefined,
        name:                    form.name.trim(),
        age:                     Number(form.age),
        gender:                  form.gender,
        city:                    form.city,
        blood_group:             form.blood_group || null,
        comorbidities:           form.comorbidities,
        insurance_provider:      form.insurance_provider || null,
        insurance_coverage:      Number(form.insurance_coverage) || 0,
        income_band:             form.income_band || null,
        emergency_contact_name:  form.emergency_contact_name || null,
        emergency_contact_phone: form.emergency_contact_phone || null,
      })

      const savedUserId = registerResult.user_id || userId
      if (savedUserId !== userId) {
        persistUserId(savedUserId)
        setStoreUserId(savedUserId)
      }

      // 2 — save financials if entered
      if (form.monthly_income) {
        await saveFinancials({
          user_id:          savedUserId,
          employment_type:  form.employment_type || 'salaried',
          monthly_income:   Number(form.monthly_income),
          existing_emi:     Number(form.existing_emi) || 0,
          cibil_score:      Number(form.cibil_score) || 700,
          employment_years: Number(form.employment_years) || 1,
        })
      }

      // 3 — reload profile into store
      const { profile, financials } = await getProfile(savedUserId)
      setProfile(profile)
      if (financials) setFinancials(financials)

      markRegistered()
      setDone(true)
    } catch (err) {
      toast(err.message || 'Registration failed. Please try again.', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="app-content">
        <StepDone name={form.name} onGo={() => navigate('/chat')} />
      </div>
    )
  }

  const stepProps = { form, update, loading }

  return (
    <div className="app-content" style={{ maxWidth: 600 }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'var(--text-2xl)',
          fontWeight: 700,
          marginBottom: 6,
        }}>
          {isRegistered() ? 'Update your profile' : 'Set up your profile'}
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
          MedPath AI uses this to personalise hospital recommendations and cost estimates.
          You only fill this once.
        </p>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <div className="card" style={{ padding: 'var(--space-8)' }}>
        {step === 0 && (
          <StepHealthProfile
            {...stepProps}
            onNext={() => setStep(1)}
          />
        )}
        {step === 1 && (
          <StepComorbidities
            {...stepProps}
            onBack={() => setStep(0)}
            onNext={() => setStep(2)}
          />
        )}
        {step === 2 && (
          <StepInsurance
            {...stepProps}
            onBack={() => setStep(1)}
            onNext={() => setStep(3)}
          />
        )}
        {step === 3 && (
          <StepFinancials
            {...stepProps}
            onBack={() => setStep(2)}
            onNext={() => setStep(4)}
          />
        )}
        {step === 4 && (
          <StepEmergencyContact
            {...stepProps}
            onBack={() => setStep(3)}
            onFinish={handleFinish}
          />
        )}
      </div>
    </div>
  )
}
