import { useEffect, useState } from 'react'
import NavBar from '../components/NavBar'
import { api } from '../services/api'

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'condition', label: 'Conditions' },
  { value: 'medication', label: 'Medications' },
  { value: 'allergy', label: 'Allergies' },
  { value: 'symptom', label: 'Symptoms' },
  { value: 'surgery', label: 'Surgeries' },
  { value: 'family_history', label: 'Family History' },
  { value: 'other', label: 'Other' },
]

const CATEGORY_LABELS = Object.fromEntries(
  CATEGORIES.slice(1).map((c) => [c.value, c.label])
)

const EMPTY_FORM = {
  category: 'condition',
  title: '',
  description: '',
  start_date: '',
  end_date: '',
}

export default function HistoryPage() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  function fetchEntries(category = activeCategory) {
    setLoading(true)
    const path = category ? `/history?category=${category}` : '/history'
    api.get(path)
      .then((data) => setEntries(data.entries || []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchEntries(activeCategory)
  }, [activeCategory])

  async function handleAdd(e) {
    e.preventDefault()
    setFormError('')

    if (!form.description.trim()) {
      setFormError('Description is required.')
      return
    }

    setSubmitting(true)

    const payload = { ...form }
    if (!payload.title) delete payload.title
    if (!payload.start_date) delete payload.start_date
    if (!payload.end_date) delete payload.end_date

    try {
      const newEntry = await api.post('/history', payload)
      setEntries((prev) => [newEntry, ...prev])
      setShowForm(false)
      setForm(EMPTY_FORM)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id) {
    setDeletingId(id)
    try {
      await api.delete(`/history/${id}`)
      setEntries((prev) => prev.filter((e) => e.id !== id))
    } catch (_) {
      // silently ignore
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <NavBar />
      <main className="page">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '0.5rem',
          }}
        >
          <h1 className="page-title" style={{ marginBottom: 0 }}>Medical History</h1>
          <button
            id="add-history-btn"
            className="btn btn-primary"
            onClick={() => { setShowForm((v) => !v); setFormError('') }}
          >
            {showForm ? 'Cancel' : '+ Add entry'}
          </button>
        </div>
        <p className="page-subtitle">Your conditions, medications, allergies, and more.</p>

        {/* Add entry form */}
        {showForm && (
          <div className="add-panel">
            <div className="add-panel-title">New history entry</div>
            <form onSubmit={handleAdd} id="add-history-form">
              <div className="form-grid" style={{ marginBottom: '1rem' }}>
                <div className="form-group">
                  <label htmlFor="h-category">Category *</label>
                  <select
                    id="h-category"
                    className="input"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    required
                  >
                    {CATEGORIES.slice(1).map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="h-title">Title (optional)</label>
                  <input
                    id="h-title"
                    className="input"
                    type="text"
                    placeholder="e.g. Type 2 Diabetes"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                  />
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label htmlFor="h-description">Description *</label>
                  <input
                    id="h-description"
                    className="input"
                    type="text"
                    placeholder="Brief details about this entry"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="h-start">Start date (optional)</label>
                  <input
                    id="h-start"
                    className="input"
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="h-end">End date (optional)</label>
                  <input
                    id="h-end"
                    className="input"
                    type="date"
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  />
                </div>
              </div>

              {formError && <div className="error-msg" style={{ marginBottom: '0.75rem' }}>{formError}</div>}

              <button
                id="submit-history-btn"
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting ? <span className="spinner" /> : 'Save entry'}
              </button>
            </form>
          </div>
        )}

        {/* Category tabs */}
        <div className="tabs">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              className={'tab' + (activeCategory === c.value ? ' active' : '')}
              onClick={() => setActiveCategory(c.value)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Entry list */}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <div className="spinner" />
          </div>
        ) : entries.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              padding: '3rem',
              border: '1px dashed var(--color-border)',
              borderRadius: 'var(--radius)',
            }}
          >
            No entries yet.{' '}
            <button
              className="btn btn-ghost"
              style={{ display: 'inline', padding: 0, border: 'none', color: 'var(--color-primary)' }}
              onClick={() => setShowForm(true)}
            >
              Add your first entry
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {entries.map((entry) => (
              <div key={entry.id} className="history-entry">
                <div style={{ flex: 1 }}>
                  <div className="history-entry-meta">
                    <span className="badge badge-other">
                      {CATEGORY_LABELS[entry.category] || entry.category}
                    </span>
                  </div>
                  {entry.title && (
                    <div className="history-entry-title">{entry.title}</div>
                  )}
                  <div className="history-entry-desc">{entry.description}</div>
                  {(entry.start_date || entry.end_date) && (
                    <div className="history-entry-dates">
                      {entry.start_date && `From ${entry.start_date}`}
                      {entry.start_date && entry.end_date && ' · '}
                      {entry.end_date ? `Until ${entry.end_date}` : entry.start_date ? '· Ongoing' : ''}
                    </div>
                  )}
                </div>

                <button
                  className="btn btn-danger"
                  style={{ flexShrink: 0, padding: '0.375rem 0.75rem', fontSize: '0.8125rem' }}
                  onClick={() => handleDelete(entry.id)}
                  disabled={deletingId === entry.id}
                >
                  {deletingId === entry.id ? <span className="spinner" style={{ width: '1rem', height: '1rem' }} /> : 'Delete'}
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  )
}
