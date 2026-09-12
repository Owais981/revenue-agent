import { Navigate, Route, Routes } from 'react-router-dom'
import { ToastProvider } from './context/ToastContext'
import ProtectedRoute from './components/ProtectedRoute'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Leads from './pages/Leads'
import LeadNew from './pages/LeadNew'
import LeadDetail from './pages/LeadDetail'
import Accounts from './pages/Accounts'
import Research from './pages/Research'
import Settings from './pages/Settings'
import AuditLogs from './pages/AuditLogs'

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/leads/new" element={<LeadNew />} />
          <Route path="/leads/:id" element={<LeadDetail />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/research" element={<Research />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ToastProvider>
  )
}
