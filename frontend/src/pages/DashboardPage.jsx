import { useEffect, useState } from 'react'
import NavBar from '../components/NavBar'
import { api } from '../services/api'
import {
  formatDate,
  reportHasResults,
  reportStatusBadgeClass,
  reportStatusLabel,
  statusBadgeClass,
  statusLabel,
} from '../utils/helpers'

// ── Helpers ───────────────────────────────────────────────────────────────────

// "2026-01-10" → a local date (new Date("2026-01-10") is UTC midnight and can
// show the previous day in timezones behind UTC)
function parseDay(day) {
  if (!day) return null
  const [y, m, d] = day.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d)
}

function shortDay(day) {
  const d = parseDay(day)
  return d ? d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : ''
}

function fullDay(day) {
  const d = parseDay(day)
  return d ? d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : ''
}

function num(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function fmt(v) {
  const n = num(v)
  if (n === null) return '—'
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100)
}

const STATUS_COLOR = {
  NORMAL: 'var(--color-success)',
  LOW: 'var(--color-warning)',
  HIGH: 'var(--color-danger)',
  CRITICAL: 'var(--color-danger)',
}

function pointColor(status) {
  return STATUS_COLOR[status?.toUpperCase()] || 'var(--color-primary)'
}

function ageFrom(dob) {
  const d = parseDay(dob)
  if (!d) return null
  const today = new Date()
  let age = today.getFullYear() - d.getFullYear()
  if (today.getMonth() < d.getMonth() || (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())) age--
  return age
}

// ── SVG Trend Chart ───────────────────────────────────────────────────────────
// Works with any number of readings: one reading is drawn as a single point
// against the normal range, two or more as a line.

function TrendChart({ data }) {
  const [hoveredIndex, setHoveredIndex] = useState(null)

  const points = (data || []).filter((d) => num(d.value) !== null)
  if (points.length === 0) {
    return (
      <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No readings for this test yet.
      </div>
    )
  }

  // Normal range from the most recent reading that has one
  const withRange = [...points].reverse().find((d) => num(d.reference_min) !== null || num(d.reference_max) !== null)
  const refMin = withRange ? num(withRange.reference_min) : null
  const refMax = withRange ? num(withRange.reference_max) : null

  // Y scale covers every value and the normal range, so even one reading has context
  const values = points.map((d) => num(d.value))
  const scaleValues = [...values, refMin, refMax].filter((v) => v !== null)
  const lo = Math.min(...scaleValues)
  const hi = Math.max(...scaleValues)
  const spread = hi - lo || Math.abs(hi) * 0.2 || 1
  const chartMin = Math.max(0, lo - spread * 0.15)
  const chartMax = hi + spread * 0.15
  const chartRange = chartMax - chartMin || 1

  const width = 600, height = 240
  const padLeft = 48, padRight = 20, padTop = 20, padBottom = 40
  const plotWidth = width - padLeft - padRight
  const plotHeight = height - padTop - padBottom
  const yFor = (v) => padTop + plotHeight - ((v - chartMin) / chartRange) * plotHeight

  const pts = points.map((d, i) => ({
    ...d,
    x: padLeft + (points.length > 1 ? (i / (points.length - 1)) * plotWidth : plotWidth / 2),
    y: yFor(num(d.value)),
  }))

  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ')
  const areaD = pts.length > 1
    ? `${pathD} L ${pts[pts.length - 1].x},${padTop + plotHeight} L ${pts[0].x},${padTop + plotHeight} Z`
    : ''

  // Normal-range band (open-ended ranges such as "< 200" run to the chart edge)
  const bandTop = yFor(refMax !== null ? Math.min(refMax, chartMax) : chartMax)
  const bandBottom = yFor(refMin !== null ? Math.max(refMin, chartMin) : chartMin)
  const showBand = withRange && bandBottom > bandTop

  // Avoid crowded date labels when there are many readings
  const labelEvery = Math.max(1, Math.ceil(pts.length / 8))
  const unit = points[points.length - 1].unit || ''

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '260px', overflow: 'visible' }}
        role="img" aria-label={`Trend chart with ${pts.length} reading${pts.length === 1 ? '' : 's'}`}>
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {showBand && (
          <g>
            <rect x={padLeft} y={bandTop} width={plotWidth} height={bandBottom - bandTop}
              fill="var(--color-success)" opacity="0.1" />
            {refMax !== null && refMax <= chartMax && (
              <line x1={padLeft} y1={bandTop} x2={width - padRight} y2={bandTop}
                stroke="var(--color-success)" strokeOpacity="0.6" strokeDasharray="6 4" strokeWidth="1.25" />
            )}
            {refMin !== null && refMin > chartMin && (
              <line x1={padLeft} y1={bandBottom} x2={width - padRight} y2={bandBottom}
                stroke="var(--color-success)" strokeOpacity="0.6" strokeDasharray="6 4" strokeWidth="1.25" />
            )}
            <text x={width - padRight - 6} y={bandTop + 13} textAnchor="end" fontSize="10"
              fill="var(--color-success)" opacity="0.9">Normal range</text>
          </g>
        )}

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
        {unit && (
          <text x={padLeft - 8} y={padTop - 8} textAnchor="end" fontSize="10" fill="var(--color-text-muted)">{unit}</text>
        )}

        {areaD && <path d={areaD} fill="url(#chartGradient)" />}
        {pts.length > 1 && (
          <path d={pathD} fill="none" stroke="var(--color-primary)" strokeWidth="3"
            strokeLinecap="round" strokeLinejoin="round" />
        )}

        {pts.map((pt, i) => (
          <g key={i} style={{ cursor: 'pointer' }}
            onMouseEnter={() => setHoveredIndex(i)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <circle cx={pt.x} cy={pt.y} r="14" fill="transparent" />
            <circle cx={pt.x} cy={pt.y}
              r={hoveredIndex === i ? 7 : pts.length === 1 ? 6 : 5}
              fill="var(--color-surface)"
              stroke={pointColor(pt.status)}
              strokeWidth={hoveredIndex === i ? 3.5 : 2.5} />
            {(i % labelEvery === 0 || i === pts.length - 1) && (
              <text x={pt.x} y={height - 10} textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">
                {shortDay(pt.date)}
              </text>
            )}
          </g>
        ))}
      </svg>

      {hoveredIndex !== null && pts[hoveredIndex] && (
        <div style={{
          position: 'absolute',
          left: `${(pts[hoveredIndex].x / width) * 100}%`,
          top: `${(pts[hoveredIndex].y / height) * 100}%`,
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
          <div style={{ fontWeight: 600, color: pointColor(pts[hoveredIndex].status) }}>
            {fmt(pts[hoveredIndex].value)} {pts[hoveredIndex].unit || ''}
            {pts[hoveredIndex].status ? ` · ${statusLabel(pts[hoveredIndex].status)}` : ''}
          </div>
          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.6875rem' }}>
            {fullDay(pts[hoveredIndex].date)}
            {pts[hoveredIndex].file_name ? ` · ${pts[hoveredIndex].file_name}` : ''}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Latest value / change summary (useful with only 1–2 readings) ────────────

function TrendSummary({ data }) {
  const points = (data || []).filter((d) => num(d.value) !== null)
  if (points.length === 0) return null

  const latest = points[points.length - 1]
  const prev = points.length > 1 ? points[points.length - 2] : null
  const unit = latest.unit || ''
  const refMin = num(latest.reference_min)
  const refMax = num(latest.reference_max)
  const rangeText = refMin !== null && refMax !== null ? `${fmt(refMin)} – ${fmt(refMax)} ${unit}`
    : refMax !== null ? `below ${fmt(refMax)} ${unit}`
    : refMin !== null ? `above ${fmt(refMin)} ${unit}`
    : 'Not available'

  let change = null
  if (prev) {
    const diff = num(latest.value) - num(prev.value)
    const pct = num(prev.value) ? (diff / Math.abs(num(prev.value))) * 100 : null
    const arrow = diff > 0 ? '▲' : diff < 0 ? '▼' : '■'
    change = `${arrow} ${diff > 0 ? '+' : ''}${fmt(diff)} ${unit}${pct !== null && diff !== 0 ? ` (${diff > 0 ? '+' : ''}${Math.round(pct)}%)` : ''}`
  }

  const cell = { display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: '120px' }
  const label = { fontSize: '0.75rem', color: 'var(--color-text-muted)' }

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div style={cell}>
          <span style={label}>Latest ({fullDay(latest.date)})</span>
          <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>
            {fmt(latest.value)} <span style={{ fontSize: '0.8125rem', fontWeight: 400 }}>{unit}</span>
            {latest.status && (
              <span className={`badge ${statusBadgeClass(latest.status)}`} style={{ marginLeft: '0.5rem', verticalAlign: 'middle' }}>
                {statusLabel(latest.status)}
              </span>
            )}
          </span>
        </div>
        <div style={cell}>
          <span style={label}>Since previous reading</span>
          <span style={{ fontSize: '1rem', fontWeight: 500 }}>{change || '—'}</span>
        </div>
        <div style={cell}>
          <span style={label}>Normal range</span>
          <span style={{ fontSize: '1rem', fontWeight: 500 }}>{rangeText}</span>
        </div>
      </div>
      {points.length === 1 && (
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>
          This is your first reading for this test. Upload another report that includes it to see how it changes over time.
        </p>
      )}
    </div>
  )
}

// ── Profile completeness (what the AI and normal ranges use) ─────────────────

function ProfileContextCard({ profile, historyCount }) {
  if (!profile) return null
  const age = ageFrom(profile.date_of_birth)
  const sexKnown = profile.sex === 'male' || profile.sex === 'female'
  const missing = []
  if (age === null) missing.push('date of birth')
  if (!sexKnown) missing.push('sex')

  const item = { display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: '110px' }
  const label = { fontSize: '0.75rem', color: 'var(--color-text-muted)' }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Your Health Profile</h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
            Used to pick your normal ranges and to tailor AI explanations
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <a href="/profile" className="btn btn-ghost" style={{ fontSize: '0.8125rem' }}>Edit profile</a>
          <a href="/history" className="btn btn-ghost" style={{ fontSize: '0.8125rem' }}>Medical history</a>
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', marginTop: '1rem' }}>
        <div style={item}><span style={label}>Age</span><span style={{ fontWeight: 500 }}>{age ?? 'Not set'}</span></div>
        <div style={item}>
          <span style={label}>Sex</span>
          <span style={{ fontWeight: 500 }}>{sexKnown ? profile.sex[0].toUpperCase() + profile.sex.slice(1) : 'Not set'}</span>
        </div>
        <div style={item}>
          <span style={label}>History entries</span>
          <span style={{ fontWeight: 500 }}>{historyCount ?? '—'}</span>
        </div>
      </div>
      {missing.length > 0 && (
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-warning)', marginTop: '1rem' }}>
          Add your {missing.join(' and ')} so normal ranges and explanations match you.
          New explanations use the update automatically.
        </p>
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
  const [trendTests, setTrendTests] = useState([])   // tests this patient has data for
  const [profile, setProfile] = useState(null)
  const [historyCount, setHistoryCount] = useState(null)
  const [selectedTest, setSelectedTest] = useState(null)
  const [trends, setTrends] = useState([])
  const [loading, setLoading] = useState(true)
  const [trendLoading, setTrendLoading] = useState(false)

  const totalReports = reports.length

  // Page data, loaded once
  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get('/reports').catch(() => []),
      api.get('/patients/me/trends/tests').catch(() => []),
      api.get('/patients/me').catch(() => null),
      api.get('/history').catch(() => null),
    ])
      .then(([reportsData, testsData, profileData, historyData]) => {
        setReports(reportsData || [])
        const tests = Array.isArray(testsData) ? testsData : []
        setTrendTests(tests)
        setProfile(profileData)
        setHistoryCount(historyData ? (historyData.total ?? historyData.entries?.length ?? 0) : null)
        // Default to the test with the most readings, so the chart isn't empty
        setSelectedTest(tests[0]?.value || null)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // Readings for the selected test
  useEffect(() => {
    if (!selectedTest) return
    setTrendLoading(true)
    api.get(`/patients/me/trends?test_name=${encodeURIComponent(selectedTest)}`)
      .then((data) => setTrends(Array.isArray(data) ? data : []))
      .catch(() => setTrends([]))
      .finally(() => setTrendLoading(false))
  }, [selectedTest])

  const testOptions = trendTests.map((t) => ({ value: t.value, label: `${t.label} (${t.count})` }))

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
              {[1, 2, 3].map(i => (
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
                <div className="stat-value">{reports.filter(r => reportHasResults(r.processing_status)).length}</div>
              </div>
              <div className="card stat-card">
                <div className="stat-label">Tests Tracked</div>
                <div className="stat-value">{trendTests.length}</div>
              </div>
            </div>

            {/* Historical Trends */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Historical Trends</h2>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                    {trendTests.length > 0
                      ? 'Track changes in your lab values over time. The number shows how many readings you have.'
                      : 'Track changes in your lab values over time'}
                  </p>
                </div>
                {trendTests.length > 0 && (
                <select
                  className="input"
                  style={{ width: 'auto', minWidth: '160px' }}
                  value={selectedTest || ''}
                  onChange={(e) => setSelectedTest(e.target.value)}
                  aria-label="Choose a test"
                >
                  {testOptions.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
                )}
              </div>

              {trendTests.length === 0 ? (
                <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                  No test results yet.{' '}
                  <a href="/upload" style={{ color: 'var(--color-primary)' }}>Upload a report</a>{' '}
                  and your values will appear here, even from a single report.
                </div>
              ) : (
                <div style={{ minHeight: '260px', opacity: trendLoading ? 0.5 : 1, transition: 'opacity 0.15s' }}>
                  <TrendSummary data={trends} />
                  <TrendChart data={trends} />
                </div>
              )}
            </div>

            <ProfileContextCard profile={profile} historyCount={historyCount} />

            {/* Recent Reports */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Recent Reports</h2>
                <a href="/reports" className="btn btn-ghost" style={{ fontSize: '0.8125rem' }}>View All</a>
              </div>
              {reports.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {reports.slice(0, 5).map((report) => (
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
                        <span className={`badge ${reportStatusBadgeClass(report.processing_status)}`}>
                          {reportStatusLabel(report.processing_status)}
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
