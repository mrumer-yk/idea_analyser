// A stable, anonymous per-browser identifier used to scope run history to the
// browser that created it. Persisted in localStorage; generated on first use.
// This is isolation, not authentication — it identifies a browser, not a person.

const KEY = 'iv_client_id'

function generate() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  // Fallback for older browsers.
  return 'cid-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

let cached = null

export function getClientId() {
  if (cached) return cached
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = generate()
      localStorage.setItem(KEY, id)
    }
    cached = id
    return id
  } catch {
    // localStorage unavailable (private mode / disabled) — fall back to a
    // per-session id so the app still works, just without cross-reload history.
    cached = cached || generate()
    return cached
  }
}
