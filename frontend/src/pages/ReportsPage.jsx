import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import { api } from '../services/api'

export default function ReportsPage() {
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/reports')
      .then((data) => setReports(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <NavBar />
      <main className="page">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h1 className="page-title">My Lab Reports</h1>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/upload')}
          >
            + Upload Report
          </button>
        </div>
        <p className="page-subtitle">View and manage your processed lab reports.</p>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <div className="spinner" />
          </div>
        ) : error ? (
          <div className="error-msg">{error}</div>
        ) : reports.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-muted)' }}>
            You haven't uploaded any reports yet.
            <br />
            <Link to="/upload" style={{ color: 'var(--color-primary)', marginTop: '0.5rem', display: 'inline-block' }}>
              Upload your first report
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {reports.map(report => (
              <div key={report.id} className="history-entry" onClick={() => navigate(`/reports/${report.id}`)} style={{ cursor: 'pointer' }}>
                <div style={{ flex: 1 }}>
                  <div className="history-entry-meta">
                    <span className={`badge ${
                      report.processing_status === 'completed' ? 'badge-normal' : 
                      report.processing_status === 'failed' ? 'badge-high' : 'badge-low'
                    }`}>
                      {report.processing_status}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {new Date(report.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="history-entry-title" style={{ marginTop: '0.5rem' }}>
                    {report.file_name}
                  </div>
                  {report.error_message && (
                    <div className="error-msg" style={{ marginTop: '0.5rem' }}>{report.error_message}</div>
                  )}
                </div>
                <div style={{ alignSelf: 'center', color: 'var(--color-primary)', fontSize: '1.25rem' }}>
                  →
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  )
}
