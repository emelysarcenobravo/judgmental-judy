import { useEffect, useState } from 'react'
import { api } from './api'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'

function App() {
  // undefined = still checking the session, null = logged out
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    api('/auth/me')
      .then((data) => setUser(data.user))
      .catch(() => setUser(null))
  }, [])

  async function logout() {
    await api('/auth/logout', { method: 'POST' })
    setUser(null)
  }

  if (user === undefined) {
    return (
      <main className="grid min-h-screen place-items-center bg-violet-50 text-violet-700">
        Loading…
      </main>
    )
  }

  return user ? <Dashboard user={user} onLogout={logout} /> : <AuthPage onAuth={setUser} />
}

export default App
