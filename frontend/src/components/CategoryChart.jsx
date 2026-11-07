import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { categoryFor, formatMoney } from '../money'

// Donut of this month's spending by category, from summary.by_category.
export default function CategoryChart({ byCategory, spentCents }) {
  const data = byCategory.map((row) => ({ ...categoryFor(row.category), value: row.total_cents }))

  return (
    <section className="flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
      <h2 className="text-lg font-extrabold text-violet-950">Where it went</h2>

      {data.length === 0 ? (
        <p className="rounded-xl bg-violet-50 px-4 py-6 text-center text-violet-700">
          Add an expense to see the breakdown.
        </p>
      ) : (
        <>
          <div className="relative h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data} dataKey="value" nameKey="label" innerRadius="62%" outerRadius="95%" paddingAngle={2} stroke="none">
                  {data.map((d) => (
                    <Cell key={d.id} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatMoney(value)} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
              <div>
                <p className="text-xs font-medium text-violet-600">Spent</p>
                <p className="text-xl font-extrabold text-violet-950">{formatMoney(spentCents)}</p>
              </div>
            </div>
          </div>

          <ul className="flex flex-col gap-2">
            {data.map((d) => (
              <li key={d.id} className="flex items-center gap-2 text-sm">
                <span className="h-3 w-3 rounded-full" style={{ background: d.color }} aria-hidden="true" />
                <span className="flex-1 text-violet-800">{d.label}</span>
                <span className="font-semibold text-violet-950">{formatMoney(d.value)}</span>
                <span className="w-10 text-right text-violet-500">{Math.round((d.value / spentCents) * 100)}%</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
