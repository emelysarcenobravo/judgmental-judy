import { useState } from 'react'
import { api } from '../api'
import { centsToInput, formatMoney, toCents } from '../money'

const inputClass =
  'h-11 w-full rounded-xl border border-violet-200 bg-white px-3 text-violet-950 outline-none transition placeholder:text-violet-300 focus:border-violet-500 focus:ring-4 focus:ring-violet-200'

// Monthly income plus fixed necessities (rent, phone, ...). Used for first-time
// setup and for editing later. Saves with PUT /api/budget.
export default function BudgetForm({ budget, onSaved, onCancel }) {
  const [income, setIncome] = useState(centsToInput(budget?.income_cents))
  const [rows, setRows] = useState(
    budget?.necessities?.length
      ? budget.necessities.map((n) => ({ name: n.name, amount: centsToInput(n.amount_cents) }))
      : [
          { name: 'Rent', amount: '' },
          { name: 'Phone', amount: '' },
        ],
  )
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  // Rows without an amount are skipped, so the "Rent"/"Phone" examples can be left blank.
  const filled = rows.filter((r) => r.amount.trim() !== '')
  const necessitiesTotal = filled.reduce((sum, r) => sum + (toCents(r.amount) ?? 0), 0)
  const incomeCents = toCents(income)

  function updateRow(index, field, value) {
    setRows((current) => current.map((r, i) => (i === index ? { ...r, [field]: value } : r)))
  }

  async function save(event) {
    event.preventDefault()
    setError('')
    if (incomeCents === null) return setError('Enter your monthly income.')
    const necessities = filled.map((r) => ({ name: r.name.trim(), amount_cents: toCents(r.amount) }))
    if (necessities.some((n) => !n.name || n.amount_cents === null)) {
      return setError('Each necessity needs a name and an amount.')
    }
    setSaving(true)
    try {
      const data = await api('/budget', { method: 'PUT', body: { income_cents: incomeCents, necessities } })
      onSaved(data.budget)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-6 rounded-3xl bg-white p-6 shadow-sm shadow-violet-100 sm:p-8">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-extrabold tracking-tight text-violet-950">
          {budget ? 'Edit your budget' : 'First, the basics'}
        </h2>
        <p className="text-violet-700">
          Judy needs to know what comes in and what has to go out before she can judge the rest.
        </p>
      </div>

      <label className="flex flex-col gap-1.5 text-sm font-medium text-violet-950">
        Monthly income
        <div className="relative">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-violet-400">$</span>
          <input
            className={`${inputClass} pl-7`}
            inputMode="decimal"
            placeholder="2,500"
            value={income}
            onChange={(e) => setIncome(e.target.value)}
            autoFocus={!budget}
          />
        </div>
      </label>

      <fieldset className="flex flex-col gap-3">
        <legend className="mb-1 text-sm font-medium text-violet-950">
          Necessities <span className="font-normal text-violet-600">(bills you can&apos;t skip)</span>
        </legend>
        {rows.map((row, index) => (
          <div key={index} className="flex gap-2">
            <input
              className={inputClass}
              aria-label={`Necessity ${index + 1} name`}
              placeholder="Rent"
              value={row.name}
              onChange={(e) => updateRow(index, 'name', e.target.value)}
            />
            <div className="relative w-36 shrink-0">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-violet-400">$</span>
              <input
                className={`${inputClass} pl-7`}
                aria-label={`Necessity ${index + 1} amount`}
                inputMode="decimal"
                placeholder="0"
                value={row.amount}
                onChange={(e) => updateRow(index, 'amount', e.target.value)}
              />
            </div>
            <button
              type="button"
              aria-label={`Remove necessity ${index + 1}`}
              onClick={() => setRows((current) => current.filter((_, i) => i !== index))}
              className="h-11 w-11 shrink-0 rounded-xl text-violet-400 transition hover:bg-violet-50 hover:text-violet-700"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => setRows((current) => [...current, { name: '', amount: '' }])}
          className="self-start rounded-xl px-3 py-2 text-sm font-bold text-violet-700 transition hover:bg-violet-50"
        >
          + Add necessity
        </button>
      </fieldset>

      {incomeCents !== null && (
        <p className="rounded-2xl bg-violet-50 px-4 py-3 text-sm text-violet-800">
          That leaves <strong className="text-violet-950">{formatMoney(incomeCents - necessitiesTotal)}</strong> of
          fun money a month. Judy will be watching it.
        </p>
      )}

      {error && (
        <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={saving}
          className="h-12 rounded-xl bg-violet-700 px-6 font-bold text-white transition hover:bg-violet-800 disabled:opacity-60"
        >
          {saving ? 'Saving…' : budget ? 'Save budget' : 'Start tracking'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="h-12 rounded-xl border border-violet-200 px-6 font-bold text-violet-800 transition hover:bg-violet-100"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
