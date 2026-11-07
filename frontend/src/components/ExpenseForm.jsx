import { useState } from 'react'
import { api } from '../api'
import { CATEGORIES, toCents, todayISO } from '../money'

const inputClass =
  'h-11 w-full rounded-xl border border-violet-200 bg-white px-3 text-violet-950 outline-none transition placeholder:text-violet-300 focus:border-violet-500 focus:ring-4 focus:ring-violet-200'

// Adds one discretionary expense with POST /api/expenses.
export default function ExpenseForm({ onAdded }) {
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('food')
  const [note, setNote] = useState('')
  const [spentOn, setSpentOn] = useState(todayISO())
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function add(event) {
    event.preventDefault()
    setError('')
    const cents = toCents(amount)
    if (!cents) return setError('Enter an amount greater than $0.')
    setSaving(true)
    try {
      const data = await api('/expenses', {
        method: 'POST',
        body: { amount_cents: cents, category, note, spent_on: spentOn },
      })
      setAmount('')
      setNote('')
      onAdded(data.expense)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={add} className="flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
      <h2 className="text-lg font-extrabold text-violet-950">Add an expense</h2>

      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Category">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            role="radio"
            aria-checked={category === c.id}
            onClick={() => setCategory(c.id)}
            className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${
              category === c.id
                ? 'border-violet-700 bg-violet-700 text-white'
                : 'border-violet-200 bg-white text-violet-800 hover:bg-violet-50'
            }`}
          >
            <span aria-hidden="true">{c.emoji}</span> {c.label}
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-[9rem_1fr_11rem]">
        <label className="flex flex-col gap-1.5 text-sm font-medium text-violet-950">
          What was it? <span className="sr-only">(optional)</span>
          <input
            className={inputClass}
            placeholder="Boba, again"
            maxLength={120}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium text-violet-950">
          Amount
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-violet-400">$</span>
            <input
              className={`${inputClass} pl-7`}
              inputMode="decimal"
              placeholder="8.50"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium text-violet-950">
          Date
          <input
            className={inputClass}
            type="date"
            max={todayISO()}
            value={spentOn}
            onChange={(e) => setSpentOn(e.target.value)}
          />
        </label>
      </div>

      {error && (
        <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={saving}
        className="h-11 self-start rounded-xl bg-violet-700 px-6 font-bold text-white transition hover:bg-violet-800 disabled:opacity-60"
      >
        {saving ? 'Adding…' : 'Add expense'}
      </button>
    </form>
  )
}
