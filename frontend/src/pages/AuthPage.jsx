import { useState } from 'react'
import { api } from '../api'

function Field({ label, ...props }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm font-medium text-violet-950">
      {label}
      <input
        {...props}
        required
        className="h-12 rounded-xl border border-violet-200 bg-white px-4 text-base text-violet-950 outline-none transition placeholder:text-violet-300 focus:border-violet-500 focus:ring-4 focus:ring-violet-200"
      />
    </label>
  )
}

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const isSignup = mode === 'signup'

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const body = isSignup ? form : { email: form.email, password: form.password }
      const data = await api(`/auth/${mode}`, { method: 'POST', body })
      onAuth(data.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function switchMode() {
    setMode(isSignup ? 'login' : 'signup')
    setError('')
  }

  return (
    <main className="grid min-h-screen bg-violet-50 lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-violet-950 p-12 text-white lg:flex">
        <p className="text-lg font-bold tracking-tight">Judgmental Judy</p>
        <div className="flex flex-col gap-4">
          <h1 className="text-5xl font-extrabold leading-tight tracking-tight">
            Your finances called.
            <span className="block text-violet-300">Judy has some questions.</span>
          </h1>
          <p className="max-w-md text-lg text-violet-200">
            Track your spending, see what’s left, and get honest (and slightly judgmental) advice.
          </p>
        </div>
        <p className="text-sm text-violet-300">CSC 603/803 · San Francisco State University</p>
      </section>

      <section className="flex items-center justify-center p-6">
        <form
          onSubmit={submit}
          className="flex w-full max-w-md flex-col gap-5 rounded-3xl bg-white p-8 shadow-xl shadow-violet-200/60"
        >
          <div className="flex flex-col gap-1">
            <p className="text-sm font-bold uppercase tracking-widest text-violet-600 lg:hidden">Judgmental Judy</p>
            <h2 className="text-3xl font-extrabold tracking-tight text-violet-950">
              {isSignup ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className="text-violet-700">
              {isSignup ? 'Judy can’t judge what she can’t see.' : 'Log in to see what Judy thinks.'}
            </p>
          </div>

          {isSignup && (
            <Field label="Name" type="text" autoComplete="name" value={form.name} onChange={update('name')} />
          )}
          <Field label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} />
          <Field
            label="Password"
            type="password"
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            minLength={isSignup ? 8 : undefined}
            value={form.password}
            onChange={update('password')}
          />

          {error && (
            <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="h-12 rounded-xl bg-violet-700 font-bold text-white transition hover:bg-violet-800 disabled:opacity-60"
          >
            {loading ? 'One moment…' : isSignup ? 'Sign up' : 'Log in'}
          </button>

          <p className="text-center text-sm text-violet-700">
            {isSignup ? 'Already have an account?' : 'New here?'}{' '}
            <button type="button" onClick={switchMode} className="font-bold text-violet-700 underline underline-offset-4 hover:text-violet-950">
              {isSignup ? 'Log in' : 'Create an account'}
            </button>
          </p>
        </form>
      </section>
    </main>
  )
}
