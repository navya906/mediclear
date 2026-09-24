import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import NavBar from '../components/NavBar'
import { api } from '../services/api'

export default function ReportDetailsPage() {
  const { id } = useParams()
  const [report, setReport] = useState(null)
  const [results, setResults] = useState([])
  const [explanations, setExplanations] = useState({}) // mapping result id -> explanation
  const [explaining, setExplaining] = useState({}) // mapping result id -> boolean
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let interval;
    
    function fetchReportAndResults() {
      Promise.all([
        api.get(`/reports/${id}`),
        api.get(`/reports/${id}/results`)
      ])
        .then(([reportData, resultsData]) => {
          setReport(reportData)
          setResults(resultsData)
          
          if (reportData.processing_status === 'completed' || reportData.processing_status === 'failed') {
            clearInterval(interval)
            setLoading(false)
          }
        })
        .catch(err => {
          setError(err.message)
          clearInterval(interval)
          setLoading(false)
        })
    }

    fetchReportAndResults()
    
    // Poll every 2 seconds if not completed
    interval = setInterval(() => {
      if (report && (report.processing_status === 'uploaded' || report.processing_status === 'processing')) {
        fetchReportAndResults()
      }
    }, 2000)
    
    return () => clearInterval(interval)
  }, [id])

  async function handleExplain(resultId) {
    if (explanations[resultId]) return // already have it

    setExplaining(prev => ({ ...prev, [resultId]: true }))
    try {
      const exp = await api.post(`/results/${resultId}/explain`)
      setExplanations(prev => ({ ...prev, [resultId]: exp }))
    } catch (err) {
      alert(`Failed to get explanation: ${err.message}`)
    } finally {
      setExplaining(prev => ({ ...prev, [resultId]: false }))
    }
  }

  if (loading && !report) {
    return (
      <>
        <NavBar />
        <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem' }}>
          <div className="spinner" />
        </div>
      </>
    )
  }

  if (error) {
    return (
      <>
        <NavBar />
        <main className="page">
          <div className="error-msg">{error}</div>
        </main>
      </>
    )
  }

  const isProcessing = report.processing_status === 'uploaded' || report.processing_status === 'processing'

  return (
    <>
      <NavBar />
      <main className="page">
        <Link to="/reports" style={{ color: 'var(--color-primary)', textDecoration: 'none', marginBottom: '1rem', display: 'inline-block' }}>
          ← Back to Reports
        </Link>
        <h1 className="page-title">{report.file_name}</h1>
        <div className="history-entry-meta" style={{ marginBottom: '2rem' }}>
          <span className={`badge ${
            report.processing_status === 'completed' ? 'badge-normal' : 
            report.processing_status === 'failed' ? 'badge-high' : 'badge-low'
          }`}>
            {report.processing_status}
          </span>
          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Uploaded on {new Date(report.created_at).toLocaleString()}
          </span>
        </div>

        <div className="card" style={{ background: 'rgba(56, 189, 248, 0.08)', borderColor: 'rgba(56, 189, 248, 0.25)', marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span style={{ fontSize: '1.25rem' }}>ℹ️</span>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
            <strong style={{ color: 'var(--color-text)' }}>Informational Tool Only:</strong> MediClear provides educational explanations and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician regarding lab results.
          </div>
        </div>

        {isProcessing && (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem auto' }} />
            <p>Processing report. This might take a few seconds...</p>
          </div>
        )}

        {report.processing_status === 'failed' && (
          <div className="card" style={{ borderColor: 'var(--color-danger)' }}>
            <h3 style={{ color: 'var(--color-danger)', marginBottom: '0.5rem' }}>Processing Failed</h3>
            <p style={{ color: 'var(--color-text-muted)' }}>{report.error_message}</p>
          </div>
        )}

        {report.processing_status === 'completed' && results.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
            No lab results were detected in this report.
          </div>
        )}

        {report.processing_status === 'completed' && results.length > 0 && (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ background: 'var(--color-surface-2)', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
                <tr>
                  <th style={{ padding: '1rem' }}>Test Name</th>
                  <th style={{ padding: '1rem' }}>Value</th>
                  <th style={{ padding: '1rem' }}>Reference Range</th>
                  <th style={{ padding: '1rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map((res, i) => (
                  <React.Fragment key={res.id}>
                    <tr style={{ borderTop: i === 0 ? 'none' : '1px solid var(--color-border)' }}>
                      <td style={{ padding: '1rem', fontWeight: 500 }}>
                        {res.test_definition ? res.test_definition.display_name : res.test_name_raw}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {res.value !== null ? `${res.value} ${res.unit}` : '—'}
                      </td>
                      <td style={{ padding: '1rem', color: 'var(--color-text-muted)' }}>
                        {res.reference_text || '—'}
                      </td>
                      <td style={{ padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <span className={`badge ${
                          res.status === 'NORMAL' ? 'badge-normal' : 
                          res.status === 'LOW' || res.status === 'HIGH' ? 'badge-high' : 'badge-other'
                        }`}>
                          {res.status}
                        </span>
                        <button 
                          className="btn btn-ghost" 
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                          onClick={() => handleExplain(res.id)}
                          disabled={explaining[res.id]}
                        >
                          {explaining[res.id] ? <span className="spinner" style={{ width: '12px', height: '12px' }}/> : 'Explain'}
                        </button>
                      </td>
                    </tr>
                    
                    {/* Explanation Row */}
                    {explanations[res.id] && (
                      <tr style={{ background: 'var(--color-surface-2)' }}>
                        <td colSpan="4" style={{ padding: '1.5rem', borderBottom: '1px solid var(--color-border)' }}>
                          <div style={{ marginBottom: '1rem' }}>
                            <strong style={{ color: 'var(--color-primary)' }}>What this means:</strong>
                            <p style={{ marginTop: '0.5rem', lineHeight: 1.5 }}>{explanations[res.id].simple_explanation}</p>
                          </div>
                          
                          {explanations[res.id].why_it_matters && (
                            <div style={{ marginBottom: '1rem' }}>
                              <strong>Why it matters:</strong>
                              <p style={{ color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>{explanations[res.id].why_it_matters}</p>
                            </div>
                          )}

                          {explanations[res.id].possible_reasons && explanations[res.id].possible_reasons.length > 0 && (
                            <div style={{ marginBottom: '1rem' }}>
                              <strong>Possible factors:</strong>
                              <ul style={{ color: 'var(--color-text-muted)', marginLeft: '1.5rem', marginTop: '0.25rem' }}>
                                {explanations[res.id].possible_reasons.map((r, idx) => <li key={idx}>{r}</li>)}
                              </ul>
                            </div>
                          )}

                          {explanations[res.id].doctor_questions && explanations[res.id].doctor_questions.length > 0 && (
                            <div>
                              <strong>Questions for your doctor:</strong>
                              <ul style={{ color: 'var(--color-text-muted)', marginLeft: '1.5rem', marginTop: '0.25rem' }}>
                                {explanations[res.id].doctor_questions.map((q, idx) => <li key={idx}>{q}</li>)}
                              </ul>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  )
}
