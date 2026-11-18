import { useEffect, useState } from 'react'
import { api } from '../api'

// Judgment level (1-5, picked by backend/judy/persona.py from % of fun money left) -> look.
const LEVELS = {
  1: { emoji: '😌', badge: 'bg-emerald-100 text-emerald-800' },
  2: { emoji: '🙂', badge: 'bg-teal-100 text-teal-800' },
  3: { emoji: '🤨', badge: 'bg-amber-100 text-amber-800' },
  4: { emoji: '😒', badge: 'bg-orange-100 text-orange-800' },
  5: { emoji: '😱', badge: 'bg-rose-100 text-rose-800' },
}

// Judy's take on the month, from GET /api/commentary. `version` changes after every
// expense or budget edit, so she reacts to new spending.
export default function JudyCard({ month, version }) {
  const key = `${month}:${version}`
  const [result, setResult] = useState(null) // { key, card } or { key, error }

  useEffect(() => {
    let current = true
    api(`/commentary?month=${month}`)
      .then((card) => current && setResult({ key, card }))
      .catch((err) => current && setResult({ key, error: err.message }))
    return () => {
      current = false
    }
  }, [key, month])

  const loading = result?.key !== key
  const card = result?.card
  const look = LEVELS[card?.level] ?? LEVELS[3]

  return (
    <section
      aria-live="polite"
      aria-busy={loading}
      className="flex gap-4 rounded-2xl border border-violet-200 bg-white p-6 shadow-sm shadow-violet-100"
    >
      <span aria-hidden="true" className="text-4xl leading-none">
        {loading ? '🧐' : look.emoji}
      </span>
      <div className={`flex min-w-0 flex-1 flex-col gap-1.5 transition-opacity ${loading ? 'opacity-50' : ''}`}>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-bold uppercase tracking-widest text-violet-600">Judy says</span>
          {card && (
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold capitalize ${look.badge}`}>
              {card.level_name} · {card.level}/5
            </span>
          )}
        </div>
        {!result && <p className="text-violet-700">Judy is reviewing your choices…</p>}
        {result?.error && <p className="text-violet-700">Judy is speechless right now. ({result.error})</p>}
        {card && (
          <>
            <p className="text-xl font-extrabold text-violet-950">{card.headline}</p>
            <p className="text-violet-800">{card.roast}</p>
            <p className="text-sm text-violet-700">
              <strong className="text-violet-950">Tip:</strong> {card.tip}
            </p>
          </>
        )}
      </div>
    </section>
  )
}
