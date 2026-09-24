import { useEffect, useState } from 'react'
import NavBar from '../components/NavBar'
import { api } from '../services/api'
import { TREND_TESTS } from '../types/constants'
import { formatDate } from '../utils/helpers'

// ── SVG Trend Chart ───────────────────────────────────────────────────────────

function TrendChart({ data }) {
  const [hoveredIndex, setHoveredIndex] = useState(null)

  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        Not enough data to show a trend for this test yet.
      </div>
    )
  }

  const values = data.map((d) => Number(d.value) || 0)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const range = maxVal - minVal || 1
  const paddingY = range * 0.15
  const chartMin = Math.max(0, minVal - paddingY)
  const chartMax = maxVal + paddingY
  const chartRange = chartMax - chartMin || 1

  const width = 600, height = 240
  const padLeft = 48, padRight = 20, padTop = 20, padBottom = 40
  const plotWidth = width - padLeft - padRight
  const plotHeight = height - padTop - padBottom

  const points = data.map((d, i) => {
    const x = padLeft + (data.length > 1 ? (i / (data.length - 1)) * plotWidth : plotWidth / 2)
    const val = Number(d.value) || 0
    const y = padTop + plotHeight - ((val - chartMin) / chartRange) * plotHeight
    return { x, y, ...d }
  })

  const pathD = points.length > 1
    ? points.reduce((acc, pt, i) => i === 0 ? `M ${pt.x},${pt.y}` : `${acc} L ${pt.x},${pt.y}`, '')
    : `M ${points[0]?.x - 20},${points[0]?.y} L ${points[0]?.x + 20},${points[0]?.y}`

  const areaD = points.length > 1
    ? `${pathD} L ${points[points.length - 1].x},${padTop + plotHeight} L ${points[0].x},${padTop + plotHeight} Z`
    : ''

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '260px', overflow: 'visible' }}>
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padTop + plotHeight * ratio
          const labelVal = (chartMax - ratio * chartRange).toFixed(1)
          return (
            <g key={ratio}>
              <line x1={padLeft} y1={y} x2={width - padRight} y2={y}
                stroke="var(--color-border)" strokeDasharray="4 4" strokeWidth="1" />
              <text x={padLeft - 8} y={y + 4} textAnchor="end" fontSize="10" fill="var(--color-text-muted)">
                {labelVal}
              </text>
            </g>
          )
        })}

        {areaD && <path d={areaD} fill="url(#chartGradient)" />}

        <path d={pathD} fill="none" stroke="var(--color-primary)" strokeWidth="3"
          strokeLinecap="round" strokeLinejoin="round" />

        {points.map((pt, i) => (
          <g key={i} style={{ cursor: 'pointer' }}
            onMouseEnter={() => setHoveredIndex(i)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <circle cx={pt.x} cy={pt.y}
              r={hoveredIndex === i ? 6 : 4}
              fill="var(--color-surface)"
              stroke="var(--color-primary)"
              strokeWidth={hoveredIndex === i ? 3 : 2} />
            <text x={pt.x} y={height - 10} textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">
              {pt.date ? new Date(pt.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : ''}
            </text>
          </g>
        ))}
      </svg>

      {hoveredIndex !== null && points[hoveredIndex] && (
        <div style={{
          position: 'absolute',
          left: `${(points[hoveredIndex].x / width) * 100}%`,
          top: `${(points[hoveredIndex].y / height) * 100}%`,
          transform: 'translate(-50%, -120%)',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.375rem 0.625rem',
          fontSize: '0.75rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
          pointerEvents: 'none',
          whiteSpace: 'nowrap',
          zIndex: 10,
        }}>
          <div style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
            {points[hoveredIndex].value} {points[hoveredIndex].unit || ''}
          </div>
          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.6875rem' }}>
            {points[hoveredIndex].date ? new Date(points[hoveredIndex].date).toLocaleDateString() : ''}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Skeleton loader ───────────────────────────────────────────────────────────

function Skeleton({ width = '100%', height = '1rem', style = {} }) {
  return (
    <div className="skeleton" style={{ width, height, borderRadius: 'var(--radius-sm)', ...style }} />
  )
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [reports, setReports] = useState([])
  const [trends, setTrends] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTest, setSelectedTest] = useState(TREND_TESTS[0].value)

  // Stats derived from reports
  const totalReports = reports.length
  const abnormalCount = reports.filter(r => r.processing_status === 'completed').length  // placeholder until results fetched

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get('/reports').catch(() => []),
      api.get(`/patients/me/trends?test_name=${selectedTest}`).catch(() => []),
    ])
      .then(([reportsData, trendsData]) => {
        setReports((reportsData || []).slice(0, 5))
        setTrends(trendsData || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedTest])

  return (
    <>
      <NavBar />
      <main className="page">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Welcome back. Here's a summary of your health data.</p>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
            {/* Stats skeleton */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
              {[1, 2].map(i => (
                <div key={i} className="card">
                  <Skeleton height="0.75rem" width="60%" style={{ marginBottom: '0.75rem' }} />
                  <Skeleton height="2rem" width="40%" />
                </div>
              ))}
            </div>
            {/* Chart skeleton */}
            <div className="card">
              <Skeleton height="1.25rem" width="40%" style={{ marginBottom: '1rem' }} />
              <Skeleton height="260px" />
            </div>
            {/* Reports skeleton */}
            <div className="card">
              <Skeleton height="1.25rem" width="30%" style={{ marginBottom: '1rem' }} />
              {[1, 2, 3].map(i => (
                <Skeleton key={i} height="3.5rem" style={{ marginBottom: '0.75rem' }} />
              ))}
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>

            {/* Stats at a glance */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
              <div className="card stat-card">
                <div className="stat-label">Total Reports</div>
                <div className="stat-value">{totalReports}</div>
              </div>
              <div className="card stat-card">
                <div className="stat-label">Processed</div>
                <div className="stat-value">{reports.filter(r => r.processing_status === 'completed').length}</div>
              </div>
              <div className="card stat-card">
                <div className="stat-label">Trend Points</div>
                <div className="stat-value">{trends.length}</div>
              </div>
            </div>

            {/* Historical Trends */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Historical Trends</h2>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                    Track changes in your lab values over time
                  </p>
                </div>
                <select
                  className="input"
                  style={{ width: 'auto', minWidth: '160px' }}
                  value={selectedTest}
                  onChange={(e) => setSelectedTest(e.target.value)}
                >
                  {TREND_TESTS.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div style={{ minHeight: '260px' }}>
                <TrendChart data={trends} />
              </div>
            </div>

            {/* Recent Reports */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Recent Reports</h2>
                <a href="/reports" className="btn btn-ghost" style={{ fontSize: '0.8125rem' }}>View All</a>
              </div>
              {reports.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {reports.map((report) => (
                    <a
                      key={report.id}
                      href={`/reports/${report.id}`}
                      style={{ textDecoration: 'none' }}
                    >
                      <div className="history-entry" style={{ cursor: 'pointer' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 500, color: 'var(--color-text)' }}>{report.file_name}</div>
                          <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                            {formatDate(report.created_at)}
                          </div>
                        </div>
                        <span className={`badge badge-${report.processing_status === 'completed' ? 'normal' : report.processing_status === 'failed' ? 'high' : 'low'}`}>
                          {report.processing_status}
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '2rem 1rem' }}>
                  No reports yet.{' '}
                  <a href="/upload" style={{ color: 'var(--color-primary)' }}>Upload your first report</a>.
                </div>
              )}
            </div>

          </div>
        )}
      </main>
    </>
  )
}
