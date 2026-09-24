import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import ProfilePage from './pages/ProfilePage'
import HistoryPage from './pages/HistoryPage'
import UploadPage from './pages/UploadPage'
import ReportsPage from './pages/ReportsPage'
import ReportDetailsPage from './pages/ReportDetailsPage'
import DashboardPage from './pages/DashboardPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Protected routes */}
        <Route path="/profile"      element={<AuthGuard><ProfilePage /></AuthGuard>} />
        <Route path="/history"      element={<AuthGuard><HistoryPage /></AuthGuard>} />
        <Route path="/upload"       element={<AuthGuard><UploadPage /></AuthGuard>} />
        <Route path="/reports"      element={<AuthGuard><ReportsPage /></AuthGuard>} />
        <Route path="/reports/:id"  element={<AuthGuard><ReportDetailsPage /></AuthGuard>} />
        <Route path="/dashboard"    element={<AuthGuard><DashboardPage /></AuthGuard>} />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
