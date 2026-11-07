import { formatMoney } from '../money'

// The four numbers from GET /api/summary, plus how much fun money is left.
export default function SummaryCards({ summary }) {
  const overspent = summary.left_cents < 0
  const cards = [
    { label: 'Monthly income', value: summary.income_cents },
    { label: 'Necessities', value: summary.necessities_cents },
    { label: 'Discretionary spent', value: summary.spent_cents },
    { label: overspent ? 'Over budget by' : 'Left to spend', value: Math.abs(summary.left_cents), alert: overspent },
  ]
  // Bar color shifts as the fun money runs out.
  const barColor =
    summary.percent_left > 50 ? 'bg-emerald-500' : summary.percent_left > 20 ? 'bg-amber-400' : 'bg-rose-500'

  return (
    <section className="flex flex-col gap-5">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="flex flex-col gap-2 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
            <span className="text-sm font-medium text-violet-600">{card.label}</span>
            <span className={`text-3xl font-extrabold ${card.alert ? 'text-rose-600' : 'text-violet-950'}`}>
              {formatMoney(card.value)}
            </span>
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <span className="font-bold text-violet-950">Fun money left this month</span>
          <span className="text-sm text-violet-700">
            {formatMoney(Math.max(summary.left_cents, 0))} of {formatMoney(summary.discretionary_cents)} ·{' '}
            <strong className="text-violet-950">{summary.percent_left}%</strong>
          </span>
        </div>
        <div
          className="h-3 overflow-hidden rounded-full bg-violet-100"
          role="progressbar"
          aria-valuenow={summary.percent_left}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Fun money left this month"
        >
          <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${summary.percent_left}%` }} />
        </div>
      </div>
    </section>
  )
}
