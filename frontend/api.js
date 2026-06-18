const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

/**
 * Non-streaming call.
 * Backend route: GET /ollama/{message}
 * Returns the full response text once generation is complete.
 */
export async function fetchSimple(message, { signal } = {}) {
  const url = `${BACKEND_URL}/ollama/${encodeURIComponent(message)}`
  const res = await fetch(url, { signal })

  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`)
  }

  // The backend returns whatever `generate()` produces. It may come back as
  // plain text or as a JSON-encoded string depending on how the provider
  // wraps it, so we handle both.
  const raw = await res.text()
  try {
    const parsed = JSON.parse(raw)
    return typeof parsed === 'string' ? parsed : JSON.stringify(parsed)
  } catch {
    return raw
  }
}

/**
 * Streaming call.
 * Backend route: GET /ollama/stream/{message}
 * Backend emits Server-Sent Events shaped like: data: {"content": "..."}\n\n
 *
 * onChunk is called with each incremental piece of text as it arrives.
 * Returns the full concatenated response once the stream ends.
 */
export async function fetchStream(message, onChunk, { signal } = {}) {
  const url = `${BACKEND_URL}/ollama/stream/${encodeURIComponent(message)}`
  const res = await fetch(url, { signal })

  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`)
  }
  if (!res.body) {
    throw new Error('Streaming is not supported by this browser/response.')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let full = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE messages are separated by a blank line ("\n\n")
    const messages = buffer.split('\n\n')
    buffer = messages.pop() ?? '' // keep any incomplete trailing chunk in the buffer

    for (const raw of messages) {
      const line = raw.trim()
      if (!line.startsWith('data:')) continue

      const jsonStr = line.slice(5).trim()
      if (!jsonStr) continue

      try {
        const payload = JSON.parse(jsonStr)
        if (payload.content) {
          full += payload.content
          onChunk(payload.content)
        }
      } catch {
        // Ignore malformed SSE lines rather than killing the whole stream.
      }
    }
  }

  return full
}
