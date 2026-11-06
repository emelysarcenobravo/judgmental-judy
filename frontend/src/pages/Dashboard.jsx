// Placeholder dashboard: shows the logged-in user and a logout button.
// The budget cards, charts and chat will go here next.
export default function Dashboard({ user, onLogout }) {
  const firstName = user.name.split(' ')[0]

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
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-extrabold tracking-tight text-violet-950">Hi, {firstName}.</h1>
          <p className="text-lg text-violet-700">Judy is ready to look at your spending. Brace yourself.</p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {['Monthly income', 'Necessities', 'Discretionary spent', 'Left to spend'].map((label) => (
            <div key={label} className="flex flex-col gap-2 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
              <span className="text-sm font-medium text-violet-600">{label}</span>
              <span className="text-3xl font-extrabold text-violet-950">$—</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
