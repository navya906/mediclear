import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

/**
 * AuthGuard — wraps protected routes.
 * Shows a spinner while session loads.
 * Redirects to /login if no user is authenticated.
 */
export default function AuthGuard({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div className="spinner" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}
