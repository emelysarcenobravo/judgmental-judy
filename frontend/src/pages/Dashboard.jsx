import { useEffect, useState } from 'react'
import { api } from '../api'
import BudgetForm from '../components/BudgetForm'
import CategoryChart from '../components/CategoryChart'
import ExpenseForm from '../components/ExpenseForm'
import ExpenseList from '../components/ExpenseList'
import SummaryCards from '../components/SummaryCards'
import { monthLabel, shiftMonth, thisMonth } from '../money'

// The logged-in home page. First visit: set up a budget. After that: the month's
// numbers, adding and deleting expenses, and the spending breakdown.
export default function Dashboard({ user, onLogout }) {
  const firstName = user.name.split(' ')[0]
  const [budget, setBudget] = useState(undefined) // undefined = loading, null = not set up yet
  const [editing, setEditing] = useState(false)
  const [month, setMonth] = useState(thisMonth())
  const [data, setData] = useState(null) // { summary, expenses } for `month`
  const [version, setVersion] = useState(0) // bump to reload after a change
  const [error, setError] = useState('')

  useEffect(() => {
    api('/budget')
      .then((res) => setBudget(res.budget))
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!budget) return
    let current = true
    Promise.all([api(`/summary?month=${month}`), api(`/expenses?month=${month}`)])
      .then(([summary, list]) => {
        if (current) setData({ month, summary, expenses: list.expenses })
      })
      .catch((err) => current && setError(err.message))
    return () => {
      current = false
    }
  }, [budget, month, version])

  const reload = () => setVersion((v) => v + 1)

  async function deleteExpense(expense) {
    setError('')
    try {
      await api(`/expenses/${expense.id}`, { method: 'DELETE' })
      reload()
    } catch (err) {
      setError(err.message)
    }
  }

  function budgetSaved(saved) {
    setBudget(saved)
    setEditing(false)
    reload()
  }

  const showingCurrent = data?.month === month

  return (
    <div className="min-h-screen bg-violet-50">
      <header className="border-b border-violet-100 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <p className="text-lg font-extrabold tracking-tight text-violet-950">Judgmental Judy</p>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-violet-700 sm:inline">{user.email}</span>
            <button
              type="button"
              onClick={onLogout}
              className="h-10 rounded-xl border border-violet-200 px-4 text-sm font-bold text-violet-800 transition hover:bg-violet-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl font-extrabold tracking-tight text-violet-950">Hi, {firstName}.</h1>
            <p className="text-lg text-violet-700">Judy is ready to look at your spending. Brace yourself.</p>
          </div>
          {budget && !editing && (
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center rounded-xl border border-violet-200 bg-white">
                <button
                  type="button"
                  aria-label="Previous month"
                  onClick={() => setMonth((m) => shiftMonth(m, -1))}
                  className="h-10 w-10 rounded-l-xl text-violet-700 hover:bg-violet-50"
                >
                  ‹
                </button>
                <span className="min-w-36 px-2 text-center text-sm font-bold text-violet-950" aria-live="polite">
                  {monthLabel(month)}
                </span>
                <button
                  type="button"
                  aria-label="Next month"
                  onClick={() => setMonth((m) => shiftMonth(m, 1))}
                  disabled={month >= thisMonth()}
                  className="h-10 w-10 rounded-r-xl text-violet-700 hover:bg-violet-50 disabled:opacity-30"
                >
                  ›
                </button>
              </div>
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="h-10 rounded-xl border border-violet-200 bg-white px-4 text-sm font-bold text-violet-800 transition hover:bg-violet-100"
              >
                Edit budget
              </button>
            </div>
          )}
        </div>

        {error && (
          <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
            {error}
          </p>
        )}

        {budget === undefined && !error && <p className="text-violet-700">Loading your budget…</p>}

        {(budget === null || editing) && (
          <div className="max-w-2xl">
            <BudgetForm budget={budget} onSaved={budgetSaved} onCancel={editing ? () => setEditing(false) : null} />
          </div>
        )}

        {budget && !editing && data && (
          <div className={`flex flex-col gap-8 transition-opacity ${showingCurrent ? '' : 'opacity-60'}`}>
            <SummaryCards summary={data.summary} />
            <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
              <div className="flex flex-col gap-6">
                <ExpenseForm onAdded={reload} />
                <ExpenseList expenses={data.expenses} onDelete={deleteExpense} />
              </div>
              <CategoryChart byCategory={data.summary.by_category} spentCents={data.summary.spent_cents} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
