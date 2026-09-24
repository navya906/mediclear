import { NavLink } from 'react-router-dom'
import { supabase } from '../services/supabase'
import { useNavigate } from 'react-router-dom'

export default function NavBar() {
  const navigate = useNavigate()

  async function handleLogout() {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <nav className="nav">
      <a href="/dashboard" className="nav-logo">MediClear</a>
      <div className="nav-links">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/profile"
          className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
        >
          Profile
        </NavLink>
        <NavLink
          to="/reports"
          className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
        >
          Reports
        </NavLink>
        <NavLink
          to="/history"
          className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
        >
          History
        </NavLink>
        <button
          onClick={handleLogout}
          className="btn btn-ghost"
          style={{ fontSize: '0.8125rem', padding: '0.375rem 0.875rem' }}
        >
          Log out
        </button>
      </div>
    </nav>
  )
}
