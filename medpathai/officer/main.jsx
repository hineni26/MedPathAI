import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import '../src/styles/global.css'
import PFLDashboard from '../src/screens/PFLDashboard'
import { ToastContainer } from '../src/components/ui'
import { useUIStore } from '../src/store/uiStore'

export function PFLOfficerApp() {
  const theme = useUIStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  return (
    <>
      <PFLDashboard />
      <ToastContainer />
    </>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PFLOfficerApp />
  </StrictMode>
)
