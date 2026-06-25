// Parse a market-size string like "INR 38.10 Bn (2024)" into a comparable number.
const UNITS = [
  ['trillion', 1e12], ['tn', 1e12],
  ['billion', 1e9], ['bn', 1e9],
  ['crore', 1e7], ['cr', 1e7],
  ['million', 1e6], ['mn', 1e6],
  ['lakh', 1e5],
  ['thousand', 1e3], ['k', 1e3],
]

export function parseAmount(str) {
  if (!str || typeof str !== 'string') return null
  const lower = str.toLowerCase()
  const m = lower.match(/([\d][\d,.]*)\s*(trillion|tn|billion|bn|crore|cr|million|mn|lakh|thousand|k)?/)
  if (!m) return null
  const num = parseFloat(m[1].replace(/,/g, ''))
  if (Number.isNaN(num)) return null
  let mult = 1
  for (const [u, factor] of UNITS) {
    if (m[2] === u) { mult = factor; break }
  }
  return num * mult
}

export function hostOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '' }
}
