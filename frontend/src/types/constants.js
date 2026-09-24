/**
 * Shared constants and type reference for MediClear frontend.
 */

// ── Lab result status values ─────────────────────────────────────────────────
export const LAB_STATUSES = ['NORMAL', 'LOW', 'HIGH', 'CRITICAL', 'UNKNOWN']

// ── Patient history categories ────────────────────────────────────────────────
export const HISTORY_CATEGORIES = [
  { value: 'condition',       label: 'Condition'       },
  { value: 'medication',      label: 'Medication'      },
  { value: 'allergy',         label: 'Allergy'         },
  { value: 'symptom',         label: 'Symptom'         },
  { value: 'surgery',         label: 'Surgery'         },
  { value: 'family_history',  label: 'Family History'  },
  { value: 'other',           label: 'Other'           },
]

// ── Report processing states ──────────────────────────────────────────────────
export const REPORT_STATUSES = {
  UPLOADED:   'uploaded',
  PROCESSING: 'processing',
  COMPLETED:  'completed',
  FAILED:     'failed',
}

// ── Upload constraints ────────────────────────────────────────────────────────
export const MAX_UPLOAD_SIZE_MB = 10
export const ACCEPTED_FILE_TYPES = '.pdf,.jpg,.jpeg,.png'
export const ACCEPTED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png']

// ── Polling ───────────────────────────────────────────────────────────────────
export const POLL_INTERVAL_MS = 3000
export const MAX_POLL_ATTEMPTS = 40  // ~2 minutes

// ── Trend tests available in the dashboard selector ──────────────────────────
// These canonical names must match test_definitions.canonical_name in the DB.
export const TREND_TESTS = [
  { value: 'hemoglobin',        label: 'Hemoglobin'        },
  { value: 'wbc',               label: 'WBC'               },
  { value: 'platelets',         label: 'Platelets'         },
  { value: 'total_cholesterol', label: 'Total Cholesterol' },
  { value: 'ldl',               label: 'LDL'               },
  { value: 'hdl',               label: 'HDL'               },
  { value: 'triglycerides',     label: 'Triglycerides'     },
  { value: 'tsh',               label: 'TSH'               },
  { value: 'free_t3',           label: 'Free T3'           },
  { value: 'free_t4',           label: 'Free T4'           },
  { value: 'alt',               label: 'ALT'               },
  { value: 'ast',               label: 'AST'               },
  { value: 'creatinine',        label: 'Creatinine'        },
  { value: 'fasting_glucose',   label: 'Fasting Glucose'   },
  { value: 'hba1c',             label: 'HbA1c'             },
]
