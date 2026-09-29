import { useEffect, useState } from 'react'
import {
  ChevronRight, CircleAlert, MessageSquareText, RefreshCw,
  Users, X,
} from 'lucide-react'
import { agentApi, getApiErrorMessage } from '../api.js'

const formatDate = (value) =>
  value
    ? new Date(value).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Not available'

export default function CustomersModal({
  totalCustomers,
  totalConversations,
  onClose,
  onSelectConversation,
}) {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    agentApi
      .listConversations()
      .then(({ data }) => {
        if (!cancelled) setConversations(data)
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <section
        className="modal record-modal customers-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="customers-modal-title"
      >
        <div className="modal-heading">
          <div>
            <div className="breadcrumb modal-breadcrumb">
              <span>Overview</span>
              <ChevronRight size={13} />
              <span>Customers & Conversations</span>
            </div>
            <h2 id="customers-modal-title">Restaurant Guest Directory & Chats</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close customers directory"
          >
            <X size={18} />
          </button>
        </div>

        <div className="record-details">
          <div className="detail-meta-grid">
            <div className="detail-meta-card">
              <span className="meta-label">
                <Users size={14} /> Registered Guests
              </span>
              <strong className="meta-value highlight">{totalCustomers ?? '—'}</strong>
            </div>
            <div className="detail-meta-card">
              <span className="meta-label">
                <MessageSquareText size={14} /> AI Support Sessions
              </span>
              <strong className="meta-value highlight">{totalConversations ?? '—'}</strong>
            </div>
          </div>

          <div className="section-block">
            <h4 className="section-subtitle">
              <MessageSquareText size={15} /> Recent AI Conversations
            </h4>

            {loading && (
              <div className="modal-loading">
                <RefreshCw size={18} className="spin" />
                <span>Loading active conversation sessions…</span>
              </div>
            )}

            {error && (
              <div className="notice error-notice" role="alert">
                <CircleAlert size={17} />
                <span>{error}</span>
              </div>
            )}

            {!loading && conversations.length > 0 ? (
              <ul className="conversations-list">
                {conversations.map((c) => (
                  <li key={c.session_id} className="conversation-item">
                    <div className="conv-main">
                      <strong>{c.title || 'Untitled Conversation'}</strong>
                      <small>Session: {c.session_id.slice(0, 8)} · Updated {formatDate(c.updated_at)}</small>
                    </div>
                    <button
                      type="button"
                      className="primary-button small-btn"
                      onClick={() => onSelectConversation(c.session_id)}
                    >
                      Open in Copilot
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              !loading && <p className="empty-state">No past AI support sessions found.</p>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </section>
    </div>
  )
}
