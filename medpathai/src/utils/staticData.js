export const COMORBIDITIES = [
  { value: 'diabetes',         label: 'Diabetes',              multiplier: 0.12 },
  { value: 'hypertension',     label: 'Hypertension',          multiplier: 0.08 },
  { value: 'cardiac_history',  label: 'Cardiac History',       multiplier: 0.18 },
  { value: 'asthma',           label: 'Asthma / COPD',         multiplier: 0.05 },
  { value: 'kidney_disease',   label: 'Kidney Disease',        multiplier: 0.15 },
  { value: 'thyroid',          label: 'Thyroid Disorder',      multiplier: 0.04 },
  { value: 'obesity',          label: 'Obesity (BMI > 30)',    multiplier: 0.10 },
  { value: 'arthritis',        label: 'Arthritis',             multiplier: 0.06 },
  { value: 'cancer_history',   label: 'Cancer History',        multiplier: 0.20 },
  { value: 'anemia',           label: 'Anemia',                multiplier: 0.03 },
]

export const BLOOD_GROUPS = ['A+', 'A−', 'B+', 'B−', 'AB+', 'AB−', 'O+', 'O−']

export const INCOME_BANDS = [
  { value: 'below_3L',  label: 'Below ₹3L / year' },
  { value: '3L_6L',     label: '₹3L – ₹6L / year' },
  { value: '6L_12L',    label: '₹6L – ₹12L / year' },
  { value: '12L_25L',   label: '₹12L – ₹25L / year' },
  { value: 'above_25L', label: 'Above ₹25L / year' },
]

export const EMPLOYMENT_TYPES = [
  { value: 'salaried',      label: 'Salaried' },
  { value: 'self_employed', label: 'Self-Employed' },
  { value: 'business',      label: 'Business Owner' },
  { value: 'retired',       label: 'Retired' },
]

export const DOC_TYPES = [
  { value: 'salary_slip',    label: 'Salary Slip',     hint: 'Last 3 months' },
  { value: 'itr',            label: 'ITR',             hint: 'Last 3 years' },
  { value: 'balance_sheet',  label: 'Balance Sheet',   hint: 'For self-employed' },
  { value: 'insurance_policy', label: 'Insurance Policy', hint: 'Health / Mediclaim' },
  { value: 'cibil_report',     label: 'CIBIL Report',     hint: 'Credit report' },
  { value: 'medical_records',label: 'Medical Records', hint: 'Previous reports' },
]
