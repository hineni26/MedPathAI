import { BrowserRouter, Routes, Route, Navigate } from 'react-router'
import AppShell from './components/AppShell'
import Registration from './screens/Registrations'
import Login from './screens/Login'
import Documents from './screens/Documents'
import Chat from './screens/Chats'
import LoanHistory from './screens/LoanHistory'
import PFLDashboard from './screens/PFLDashboard'
import { isRegistered } from './api/auth'
import { getOfficerToken } from './api/session'

// Guard: redirect to /login if not authenticated
function RequireProfile({ children }) {
  return isRegistered() ? children : <Navigate to="/login" replace />
}

function RequireOfficer({ children }) {
  return getOfficerToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Registration />} />
          <Route
            path="/documents"
            element={<RequireProfile><Documents /></RequireProfile>}
          />
          <Route
            path="/chat"
            element={<RequireProfile><Chat /></RequireProfile>}
          />
          <Route
            path="/loans"
            element={<RequireProfile><LoanHistory /></RequireProfile>}
          />
          <Route
            path="/admin"
            element={<RequireOfficer><PFLDashboard /></RequireOfficer>}
          />
          <Route path="*" element={<Navigate to={isRegistered() ? '/chat' : '/login'} replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
