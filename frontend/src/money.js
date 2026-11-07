// Money is stored as whole cents (1250 = $12.50) so totals never get
// floating-point rounding errors. These helpers convert for display and forms.

const dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export function formatMoney(cents) {
  return dollars.format((cents ?? 0) / 100)
}

// "12.5" or "$1,200" from a form field -> 1250 / 120000 cents, or null if it isn't a number.
export function toCents(text) {
  const value = Number(String(text).replace(/[$,\s]/g, ''))
  return text !== '' && Number.isFinite(value) && value >= 0 ? Math.round(value * 100) : null
}

export function centsToInput(cents) {
  return cents ? String(cents / 100) : ''
}

// Must match CATEGORIES in backend/budget.py.
export const CATEGORIES = [
  { id: 'food', label: 'Food & drinks', emoji: '🧋', color: '#7c3aed' },
  { id: 'shopping', label: 'Shopping', emoji: '🛍️', color: '#c026d3' },
  { id: 'entertainment', label: 'Entertainment', emoji: '🎟️', color: '#f59e0b' },
  { id: 'subscriptions', label: 'Subscriptions', emoji: '📺', color: '#0ea5e9' },
  { id: 'transportation', label: 'Transportation', emoji: '🚌', color: '#10b981' },
  { id: 'other', label: 'Other', emoji: '✨', color: '#94a3b8' },
]

export const categoryFor = (id) => CATEGORIES.find((c) => c.id === id) ?? CATEGORIES.at(-1)

// Dates in the user's own timezone, as the API expects them.
const pad = (n) => String(n).padStart(2, '0')
export const todayISO = () => {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
export const thisMonth = () => todayISO().slice(0, 7)

// "2026-11" plus or minus whole months.
export function shiftMonth(month, by) {
  const [y, m] = month.split('-').map(Number)
  const d = new Date(y, m - 1 + by, 1)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`
}

export function monthLabel(month) {
  const [y, m] = month.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}
