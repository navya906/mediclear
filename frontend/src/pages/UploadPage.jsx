import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import { supabase } from '../services/supabase'
import { formatFileSize, isAcceptedFileType } from '../utils/helpers'
import { MAX_UPLOAD_SIZE_MB, ACCEPTED_FILE_TYPES } from '../types/constants'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)   // 0-100
  const [error, setError] = useState('')

  // ── File selection helpers ─────────────────────────────────────────────────

  function validateAndSet(selectedFile) {
    if (!selectedFile) return
    if (!isAcceptedFileType(selectedFile)) {
      setError('Unsupported file type. Please upload a PDF, JPG, or PNG.')
      return
    }
    if (selectedFile.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_UPLOAD_SIZE_MB} MB.`)
      return
    }
    setFile(selectedFile)
    setError('')
  }

  function handleFileChange(e) {
    validateAndSet(e.target.files?.[0])
  }

  // ── Drag-and-drop handlers ─────────────────────────────────────────────────

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => setDragging(false), [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    validateAndSet(e.dataTransfer.files?.[0])
  }, [])

  // ── Upload ────────────────────────────────────────────────────────────────

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) { setError('Please select a file first.'); return }

    setUploading(true)
    setError('')
    setProgress(0)

    try {
      const { data } = await supabase.auth.getSession()
      const token = data?.session?.access_token
      if (!token) throw new Error('Not authenticated. Please log in again.')

      const formData = new FormData()
      formData.append('file', file)

      // Simulate progress since fetch doesn't expose upload progress
      const progressInterval = setInterval(() => {
        setProgress((p) => (p < 85 ? p + 5 : p))
      }, 200)

      const response = await fetch(`${BASE_URL}/reports/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `Upload failed (HTTP ${response.status})`)
      }

      const report = await response.json()
      navigate(`/reports/${report.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <NavBar />
      <main className="page">
        <h1 className="page-title">Upload Lab Report</h1>
        <p className="page-subtitle">
          Upload a PDF or image of your medical lab report. We'll extract and explain your results automatically.
        </p>

        <div className="card" style={{ maxWidth: '540px' }}>
          <form onSubmit={handleUpload}>

            {/* Drag-and-drop zone */}
            <div
              className={`drop-zone${dragging ? ' drop-zone--active' : ''}${file ? ' drop-zone--filled' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !uploading && fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              aria-label="Upload file drop zone"
            >
              <input
                ref={fileInputRef}
                id="file-upload"
                type="file"
                accept={ACCEPTED_FILE_TYPES}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                disabled={uploading}
              />

              {file ? (
                <div className="drop-zone-file">
                  <span className="drop-zone-icon">📄</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{file.name}</div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                      {formatFileSize(file.size)}
                    </div>
                  </div>
                  {!uploading && (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                      onClick={(e) => { e.stopPropagation(); setFile(null) }}
                    >
                      Change
                    </button>
                  )}
                </div>
              ) : (
                <div className="drop-zone-empty">
                  <span className="drop-zone-icon">📁</span>
                  <div style={{ fontWeight: 500 }}>
                    {dragging ? 'Drop it here!' : 'Drag & drop your file here'}
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                    or <span style={{ color: 'var(--color-primary)', textDecoration: 'underline', cursor: 'pointer' }}>browse files</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                    PDF, JPG, PNG — up to {MAX_UPLOAD_SIZE_MB} MB
                  </div>
                </div>
              )}
            </div>

            {/* Progress bar */}
            {uploading && (
              <div style={{ marginTop: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                  <span>Uploading…</span>
                  <span>{progress}%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}

            {error && (
              <div className="error-msg" style={{ marginTop: '1rem' }}>{error}</div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading || !file}
              style={{ width: '100%', marginTop: '1.5rem', padding: '0.75rem' }}
            >
              {uploading ? <span className="spinner" /> : 'Upload & Process'}
            </button>
          </form>
        </div>
      </main>
    </>
  )
}
