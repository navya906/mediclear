/**
 * Shared frontend utilities for MediClear.
 */

// ── Date formatting ──────────────────────────────────────────────────────────

/**
 * Format an ISO date string as "Jan 5, 2026".
 */
export function formatDate(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Format an ISO date string as "Jan 5, 2026, 10:30 AM".
 */
export function formatDateTime(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ── Status helpers ────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  NORMAL:   { badgeClass: 'badge-normal',   label: 'Normal'   },
  LOW:      { badgeClass: 'badge-low',      label: 'Low'      },
  HIGH:     { badgeClass: 'badge-high',     label: 'High'     },
  CRITICAL: { badgeClass: 'badge-critical', label: 'Critical' },
  UNKNOWN:  { badgeClass: 'badge-other',    label: 'Unknown'  },
}

/**
 * Return the CSS badge class for a lab result status string.
 */
export function statusBadgeClass(status) {
  return (STATUS_CONFIG[status?.toUpperCase()] || STATUS_CONFIG.UNKNOWN).badgeClass
}

/**
 * Return the human-readable label for a lab result status string.
 */
export function statusLabel(status) {
  return (STATUS_CONFIG[status?.toUpperCase()] || STATUS_CONFIG.UNKNOWN).label
}

// ── Report processing status ──────────────────────────────────────────────────

const REPORT_STATUS_CONFIG = {
  completed:  { badgeClass: 'badge-normal', label: 'Completed'  },
  processing: { badgeClass: 'badge-low',    label: 'Processing' },
  uploaded:   { badgeClass: 'badge-low',    label: 'Queued'     },
  failed:     { badgeClass: 'badge-high',   label: 'Failed'     },
}

export function reportStatusBadgeClass(status) {
  return (REPORT_STATUS_CONFIG[status] || { badgeClass: 'badge-other' }).badgeClass
}

export function reportStatusLabel(status) {
  return (REPORT_STATUS_CONFIG[status] || { label: status }).label
}

// ── File helpers ──────────────────────────────────────────────────────────────

/**
 * Return a human-readable file size string.
 */
export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const ACCEPTED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']

/**
 * Return true if the file type is accepted by the backend.
 */
export function isAcceptedFileType(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  return ACCEPTED_EXTENSIONS.includes(ext)
}

// ── Misc ──────────────────────────────────────────────────────────────────────

/**
 * Truncate a string to maxLen characters, adding an ellipsis if needed.
 */
export function truncate(str, maxLen = 40) {
  if (!str || str.length <= maxLen) return str
  return str.slice(0, maxLen - 1) + '…'
}
