import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <>
      <NavBar />
      <main className="page" style={{ textAlign: 'center', paddingTop: '5rem' }}>
        <div style={{ fontSize: '5rem', marginBottom: '1rem' }}>🔬</div>
        <h1 className="page-title" style={{ fontSize: '2.5rem' }}>404</h1>
        <p className="page-subtitle" style={{ fontSize: '1rem', maxWidth: '360px', margin: '0 auto 2rem' }}>
          We couldn't find that page. It may have moved or never existed.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </button>
          <button className="btn btn-ghost" onClick={() => navigate(-1)}>
            Go Back
          </button>
        </div>
      </main>
    </>
  )
}
