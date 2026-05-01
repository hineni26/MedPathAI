import { Outlet } from 'react-router'
import { useEffect } from 'react'
import Sidebar from './Sidebar'
import TopBar from './Topbar'
import { ToastContainer } from './ui'
import { useUIStore } from '../store/uiStore'

export default function AppShell() {
  const theme = useUIStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

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
