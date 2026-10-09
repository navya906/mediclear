-- Persist the per-result "needs review" flag computed by the normalizer.
-- A result needs review when extraction confidence is below 0.75 or no usable
-- reference range was found (status UNKNOWN).
--
-- Run once in the Supabase SQL Editor for the shared project. Safe to re-run.
-- The backend works without it (it retries the insert without the column),
-- but the flag is only stored per result once this has been applied.

ALTER TABLE lab_results
    ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT FALSE;

-- Make PostgREST pick up the new column immediately.
NOTIFY pgrst, 'reload schema';
