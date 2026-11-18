import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

// What each of Judy's backend tools did, shown under her reply.
const TOOL_LABELS = {
  get_month_summary: 'checked another month',
  list_expenses: 'looked through your purchases',
  find_repeat_purchases: 'spotted repeat purchases',
}

const SUGGESTIONS = ['Roast my spending.', 'Did I spend more than last month?', 'Should I buy $120 headphones?']

// Chat with Judy through POST /api/chat. The backend looks up the user's real data
// itself, so only the conversation text and the month on screen are sent.
export default function JudyChat({ month }) {
  const [messages, setMessages] = useState([]) // [{ role, content, tools? }]
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages, sending])

  async function send(text) {
    const content = text.trim()
    if (!content || sending) return
    const next = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setError('')
    setSending(true)
    try {
      // The API takes at most 20 messages, and an odd count keeps a user message first.
      const recent = next.slice(-19).map(({ role, content }) => ({ role, content }))
      const data = await api('/chat', { method: 'POST', body: { messages: recent, month } })
      setMessages([...next, { role: 'assistant', content: data.reply, tools: data.tools_used }])
    } catch (err) {
      setMessages(messages) // drop the unanswered message so turns keep alternating
      setInput(content)
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-sm shadow-violet-100">
      <h2 className="text-lg font-extrabold text-violet-950">Ask Judy</h2>

      <div className="flex max-h-96 flex-col gap-3 overflow-y-auto" aria-live="polite">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="rounded-full border border-violet-200 px-3 py-1.5 text-sm font-medium text-violet-800 transition hover:bg-violet-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <p key={i} className="self-end rounded-2xl rounded-br-md bg-violet-700 px-4 py-2 text-white">
              {m.content}
            </p>
          ) : (
            <div key={i} className="flex flex-col gap-1 self-start">
              <p className="rounded-2xl rounded-bl-md bg-violet-50 px-4 py-2 text-violet-950">{m.content}</p>
              {m.tools?.length > 0 && (
                <p className="px-1 text-xs text-violet-500">
                  🔎 Judy {[...new Set(m.tools)].map((t) => TOOL_LABELS[t] ?? t).join(', ')}
                </p>
              )}
            </div>
          ),
        )}
        {sending && <p className="self-start px-1 text-sm text-violet-500">Judy is typing…</p>}
        <div ref={endRef} />
      </div>

      {error && (
        <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
          {error}
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex gap-2"
      >
        <label className="sr-only" htmlFor="judy-input">
          Message Judy
        </label>
        <input
          id="judy-input"
          className="h-11 min-w-0 flex-1 rounded-xl border border-violet-200 bg-white px-3 text-violet-950 outline-none transition placeholder:text-violet-300 focus:border-violet-500 focus:ring-4 focus:ring-violet-200"
          placeholder="Can I afford sushi tonight?"
          maxLength={1000}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="h-11 rounded-xl bg-violet-700 px-4 font-bold text-white transition hover:bg-violet-800 disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </section>
  )
}
