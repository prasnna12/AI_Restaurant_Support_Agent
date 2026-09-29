import { useEffect, useRef } from 'react'
import {
  Bot, CircleAlert,
  Send, Sparkles,
} from 'lucide-react'

const suggestionChips = [
  'What is the status of order ORD-1001?',
  'What is our policy for refunding delayed deliveries?',
  'How do we handle food allergy complaints?',
  'List recent high priority support tickets',
]

export default function AssistantView({
  messages,
  input,
  pending,
  status,
  profile,
  onInput,
  onSubmit,
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, pending])

  return (
    <section className="assistant-page">
      <div className="assistant-intro">
        <div>
          <div className="eyebrow">Intelligent Copilot</div>
          <h2>Restaurant Operations Assistant</h2>
          <p>
            Query real-time orders, check restaurant operational guidelines, or triage guest tickets.
          </p>
        </div>
        <div className="assistant-state">
          <span className="status-light" />
          <span>{status}</span>
        </div>
      </div>

      {/* Suggestion Chips */}
      {messages.length <= 1 && (
        <div className="suggestion-chips-strip">
          <span className="suggestion-hint">
            <Sparkles size={14} /> Quick Inquiries:
          </span>
          {suggestionChips.map((chip) => (
            <button
              key={chip}
              type="button"
              className="suggestion-chip-btn"
              onClick={() => {
                onInput(chip)
              }}
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      <div className="chat-window">
        <div
          className="chat-messages"
          aria-live="polite"
          aria-relevant="additions text"
        >
          {messages.map((message, index) => (
            <article
              className={`chat-message ${message.role}`}
              key={`${message.role}-${index}`}
            >
              <div className="chat-icon">
                {message.role === 'assistant' ? (
                  <Bot size={17} />
                ) : message.role === 'user' ? (
                  <span>{profile?.name?.slice(0, 1) || 'U'}</span>
                ) : (
                  <CircleAlert size={16} />
                )}
              </div>
              <div className="chat-copy">
                <small>
                  {message.role === 'assistant'
                    ? 'DineAssist Copilot'
                    : message.role === 'user'
                    ? profile?.name || 'You'
                    : 'System Notice'}
                </small>
                <div className="chat-bubble-text">{message.content}</div>

                {message.isFallback && (
                  <span className="response-note">Fallback response</span>
                )}

                {message.tools?.length > 0 && (
                  <div className="response-tools">
                    <span className="tools-title">Tools executed:</span>
                    {message.tools.map((tool, toolIndex) => (
                      <span key={`${tool.tool_name}-${toolIndex}`} className="tool-tag">
                        {tool.summary || tool.tool_name}
                      </span>
                    ))}
                  </div>
                )}

                {message.sources?.length > 0 && (
                  <div className="response-sources">
                    <strong>Knowledge Base Documents Referenced:</strong>
                    {message.sources.map((source) => (
                      <span key={source} className="source-pill">
                        {source}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </article>
          ))}

          {pending && (
            <div className="chat-pending" role="status">
              <span className="status-light" />
              <span>Analyzing restaurant knowledge base and records…</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <form className="chat-form" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="chat-input">
            Message the DineAssist assistant
          </label>
          <textarea
            id="chat-input"
            rows="2"
            maxLength={2000}
            value={input}
            onChange={(e) => onInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                onSubmit(e)
              }
            }}
            placeholder="Ask about an order (e.g. ORD-1001), store policy, or customer issue… (Enter to send)"
            disabled={pending}
            required
          />
          <button
            className="send-button"
            type="submit"
            aria-label="Send message"
            title="Send message"
            disabled={pending || !input.trim()}
          >
            <Send size={17} />
          </button>
        </form>
      </div>
    </section>
  )
}
