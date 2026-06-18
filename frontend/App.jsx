import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import { fetchSimple, fetchStream } from './api.js'
import './App.css'

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streamingEnabled, setStreamingEnabled] = useState(true)
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState(null)

  const scrollRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isBusy) return

    setError(null)
    setInput('')

    const userMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed }
    const assistantId = crypto.randomUUID()
    const assistantMessage = { id: assistantId, role: 'assistant', content: '', streaming: true }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setIsBusy(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      if (streamingEnabled) {
        await fetchStream(
          trimmed,
          (chunk) => {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + chunk } : m))
            )
          },
          { signal: controller.signal }
        )
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m))
        )
      } else {
        const full = await fetchSimple(trimmed, { signal: controller.signal })
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: full, streaming: false } : m))
        )
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Something went wrong talking to the backend.')
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content || '_(no response — see error below)_', streaming: false }
              : m
          )
        )
      }
    } finally {
      setIsBusy(false)
      abortRef.current = null
    }
  }

  function handleStop() {
    abortRef.current?.abort()
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-title">
          <span className="app-title-dot" />
          local llm console
        </div>

        <label className="stream-toggle">
          <span className="stream-toggle-label">stream</span>
          <button
            type="button"
            role="switch"
            aria-checked={streamingEnabled}
            className={`switch ${streamingEnabled ? 'switch--on' : ''}`}
            onClick={() => setStreamingEnabled((v) => !v)}
            disabled={isBusy}
          >
            <span className="switch-knob" />
          </button>
        </label>
      </header>

      <main className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Send a prompt to start the conversation.</p>
            <p className="empty-state-sub">
              Toggle streaming above to switch between token-by-token and full-response output.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} role={m.role} content={m.content} isStreaming={m.streaming} />
        ))}
      </main>

      {error && <div className="error-banner">{error}</div>}

      <form className="input-bar" onSubmit={handleSend}>
        <input
          type="text"
          className="input-field"
          placeholder="Ask something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isBusy}
        />
        {isBusy ? (
          <button type="button" className="send-btn send-btn--stop" onClick={handleStop}>
            Stop
          </button>
        ) : (
          <button type="submit" className="send-btn" disabled={!input.trim()}>
            Send
          </button>
        )}
      </form>
    </div>
  )
}
