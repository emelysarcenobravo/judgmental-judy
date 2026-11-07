import { categoryFor, formatMoney } from '../money'

const dateLabel = (iso) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

// This month's expenses, newest first. Deleting calls DELETE /api/expenses/:id.
export default function ExpenseList({ expenses, onDelete }) {
  return (
    <section className="flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
      <h2 className="text-lg font-extrabold text-violet-950">
        This month&apos;s spending <span className="font-medium text-violet-500">({expenses.length})</span>
      </h2>

      {expenses.length === 0 ? (
        <p className="rounded-xl bg-violet-50 px-4 py-6 text-center text-violet-700">
          Nothing yet. Judy is suspicious.
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-violet-100">
          {expenses.map((expense) => {
            const category = categoryFor(expense.category)
            return (
              <li key={expense.id} className="group flex items-center gap-3 py-3">
                <span
                  className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-lg"
                  style={{ background: `${category.color}1a` }}
                  aria-hidden="true"
                >
                  {category.emoji}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-violet-950">{expense.note || category.label}</p>
                  <p className="text-sm text-violet-600">
                    {category.label} · {dateLabel(expense.spent_on)}
                  </p>
                </div>
                <span className="font-bold text-violet-950">{formatMoney(expense.amount_cents)}</span>
                <button
                  type="button"
                  onClick={() => onDelete(expense)}
                  aria-label={`Delete ${expense.note || category.label}, ${formatMoney(expense.amount_cents)}`}
                  className="h-9 w-9 rounded-lg text-violet-300 transition hover:bg-rose-50 hover:text-rose-600 focus:text-rose-600"
                >
                  ✕
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
