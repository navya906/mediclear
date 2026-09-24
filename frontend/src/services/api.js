/**
 * Thin fetch wrapper for the MediClear FastAPI backend.
 * Automatically attaches the Supabase JWT from the current session.
 */

import { supabase } from './supabase'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function getAuthHeaders() {
  const { data } = await supabase.auth.getSession()
  const token = data?.session?.access_token
  if (!token) throw new Error('Not authenticated')
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

async function request(method, path, body) {
  const headers = await getAuthHeaders()
  const options = { method, headers }
  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  const response = await fetch(`${BASE_URL}${path}`, options)

  if (!response.ok) {
    let message = `HTTP ${response.status}`
    try {
      const json = await response.json()
      message = json.detail || message
    } catch (_) {}
    throw new Error(message)
  }

  if (response.status === 204) return null
  return response.json()
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  patch: (path, body) => request('PATCH', path, body),
  delete: (path) => request('DELETE', path),
}
