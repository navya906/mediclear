import { useEffect, useState } from 'react'
import NavBar from '../components/NavBar'
import { api } from '../services/api'

const SEX_LABELS = {
  male: 'Male',
  female: 'Female',
  other: 'Other',
  prefer_not_to_say: 'Prefer not to say',
}

export default function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ date_of_birth: '', sex: '' })

  useEffect(() => {
    api.get('/patients/me')
      .then((data) => {
        setProfile(data)
        setForm({
          date_of_birth: data.date_of_birth || '',
          sex: data.sex || '',
        })
      })
      .catch(() => setError('Could not load profile.'))
      .finally(() => setLoading(false))
  }, [])

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setError('')

    const updates = {}
    if (form.date_of_birth) updates.date_of_birth = form.date_of_birth
    if (form.sex) updates.sex = form.sex

    try {
      const updated = await api.patch('/patients/me', updates)
      setProfile(updated)
      setEditing(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <NavBar />
      <main className="page">
        <h1 className="page-title">My Profile</h1>
        <p className="page-subtitle">Your personal information and account details.</p>

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <div className="spinner" />
          </div>
        )}

        {!loading && profile && (
          <div className="card" style={{ maxWidth: '480px' }}>
            {!editing ? (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <ProfileField label="Date of Birth" value={profile.date_of_birth || '—'} />
                  <ProfileField label="Sex" value={SEX_LABELS[profile.sex] || '—'} />
                  <ProfileField
                    label="Member since"
                    value={new Date(profile.created_at).toLocaleDateString()}
                  />
                </div>
                <div style={{ marginTop: '1.5rem' }}>
                  <button
                    id="edit-profile-btn"
                    className="btn btn-primary"
                    onClick={() => setEditing(true)}
                  >
                    Edit profile
                  </button>
                </div>
              </>
            ) : (
              <form onSubmit={handleSave} id="profile-form">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div className="form-group">
                    <label htmlFor="dob">Date of Birth</label>
                    <input
                      id="dob"
                      className="input"
                      type="date"
                      value={form.date_of_birth}
                      onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="sex">Sex</label>
                    <select
                      id="sex"
                      className="input"
                      value={form.sex}
                      onChange={(e) => setForm({ ...form, sex: e.target.value })}
                    >
                      <option value="">Select…</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                      <option value="prefer_not_to_say">Prefer not to say</option>
                    </select>
                  </div>

                  {error && <div className="error-msg">{error}</div>}

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      id="save-profile-btn"
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? <span className="spinner" /> : 'Save'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => { setEditing(false); setError('') }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        )}

        {error && !loading && !profile && (
          <div className="error-msg">{error}</div>
        )}
      </main>
    </>
  )
}

function ProfileField({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
        {label}
      </div>
      <div style={{ fontWeight: 500 }}>{value}</div>
    </div>
  )
}
