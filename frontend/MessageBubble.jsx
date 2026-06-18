import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function MessageBubble({ role, content, isStreaming }) {
  const isUser = role === 'user'

  return (
    <div className={`bubble-row ${isUser ? 'bubble-row--user' : 'bubble-row--assistant'}`}>
      <div className="bubble-role">{isUser ? 'you' : 'model'}</div>
      <div className={`bubble ${isUser ? 'bubble--user' : 'bubble--assistant'}`}>
        {isUser ? (
          <p className="bubble-plain">{content}</p>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content || ' '}
            </ReactMarkdown>
            {isStreaming && <span className="cursor-blink" aria-hidden="true" />}
          </div>
        )}
      </div>
    </div>
  )
}
