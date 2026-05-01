import { Outlet } from 'react-router'
import Sidebar from './Sidebar'
import TopBar from './Topbar'
import { ToastContainer } from './ui'

export default function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <Outlet />
      </div>
      <ToastContainer />
    </div>
  )
}
