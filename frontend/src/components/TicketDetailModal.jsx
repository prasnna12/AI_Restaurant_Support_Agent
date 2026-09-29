import { useEffect, useState } from 'react'
import {
  Calendar, CheckCircle2, ChevronRight, CircleAlert, Clock3, ExternalLink,
  Package, RefreshCw, ShieldCheck, Tag, Ticket, User, Users, X,
} from 'lucide-react'
import { ticketsApi, getApiErrorMessage } from '../api.js'

const ticketStatuses = ['Open', 'In Progress', 'Resolved', 'Escalated']

const formatDate = (value) =>
  value
    ? new Date(value).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Not available'

export default function TicketDetailModal({
  ticketId,
  onClose,
  onStatusUpdated,
  onOpenOrder,
}) {
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [statusComment, setStatusComment] = useState('')
  const [updating, setUpdating] = useState(false)
  const [actionSuccess, setActionSuccess] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    ticketsApi
      .get(ticketId)
      .then(({ data }) => {
        if (!cancelled) {
          setTicket(data)
          setSelectedStatus(data.status)
        }
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
  }, [ticketId])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const handleUpdateStatus = async () => {
    if (!selectedStatus || selectedStatus === ticket?.status) return
    setUpdating(true)
    setActionSuccess('')
    setError('')

    try {
      const { data } = await ticketsApi.updateStatus(ticket.ticket_id, {
        status: selectedStatus,
        comment: statusComment.trim() || `Status updated to ${selectedStatus} from operations console.`,
      })
      setTicket(data)
      setStatusComment('')
      setActionSuccess(`Ticket status updated to "${data.status}"`)
      if (onStatusUpdated) onStatusUpdated(data)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <section
        className="modal record-modal ticket-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-detail-title"
      >
        <div className="modal-heading">
          <div>
            <div className="breadcrumb modal-breadcrumb">
              <span>Support tickets</span>
              <ChevronRight size={13} />
              <span>{ticketId}</span>
            </div>
            <h2 id="ticket-detail-title">Ticket {ticketId}</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close ticket details"
          >
            <X size={18} />
          </button>
        </div>

        {loading && (
          <div className="modal-loading">
            <RefreshCw size={18} className="spin" />
            <span>Loading support ticket from database…</span>
          </div>
        )}

        {error && (
          <div className="notice error-notice" role="alert">
            <CircleAlert size={17} />
            <span>{error}</span>
          </div>
        )}

        {actionSuccess && (
          <div className="notice success-notice" role="status">
            <CheckCircle2 size={17} />
            <span>{actionSuccess}</span>
          </div>
        )}

        {ticket && (
          <div className="record-details ticket-details-content">
            <div className="detail-meta-grid">
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Tag size={14} /> Category
                </span>
                <strong className="meta-value">{ticket.category}</strong>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <ShieldCheck size={14} /> Priority
                </span>
                <span className={`tag ${ticket.priority.toLowerCase()}`}>
                  {ticket.priority}
                </span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Ticket size={14} /> Status
                </span>
                <span
                  className={`ticket-status ${ticket.status
                    .toLowerCase()
                    .replaceAll(' ', '-')}`}
                >
                  {ticket.status}
                </span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Users size={14} /> Assigned Team
                </span>
                <strong className="meta-value">{ticket.assigned_team}</strong>
              </div>
            </div>

            <div className="ticket-header-card">
              <h3 className="ticket-title-large">{ticket.title}</h3>
              <div className="ticket-sub-refs">
                <span>
                  <User size={14} /> Customer: <strong>{ticket.customer_name || 'Guest'}</strong>
                </span>
                {ticket.order_reference ? (
                  <span>
                    <Package size={14} /> Order Ref:{' '}
                    <button
                      type="button"
                      className="link-inline"
                      onClick={() => onOpenOrder && onOpenOrder(ticket.order_reference)}
                      title="Open related order details"
                    >
                      {ticket.order_reference} <ExternalLink size={12} />
                    </button>
                  </span>
                ) : (
                  <span>No linked order</span>
                )}
                <span>
                  <Calendar size={14} /> Created: {formatDate(ticket.created_at)}
                </span>
              </div>
            </div>

            <div className="section-block">
              <h4 className="section-subtitle">Issue Description</h4>
              <div className="ticket-description-text">{ticket.description}</div>
            </div>

            {/* Timeline / Activity Section */}
            <div className="section-block">
              <h4 className="section-subtitle">
                <Clock3 size={15} /> Activity Timeline ({ticket.timeline?.length || 0})
              </h4>
              {ticket.timeline && ticket.timeline.length > 0 ? (
                <ol className="timeline">
                  {ticket.timeline.map((entry, idx) => (
                    <li key={`${entry.created_at}-${idx}`}>
                      <span className="timeline-dot" />
                      <div className="timeline-content">
                        <div className="timeline-header">
                          <strong>{entry.action}</strong>
                          <span className="actor-badge">{entry.actor}</span>
                        </div>
                        {entry.details && <p className="timeline-details">{entry.details}</p>}
                        <small className="timeline-time">{formatDate(entry.created_at)}</small>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="empty-state">No timeline events recorded yet.</p>
              )}
            </div>

            {/* Status Update Control */}
            <div className="ticket-update-box">
              <h4 className="section-subtitle">Update Ticket Status</h4>
              <div className="form-row status-update-form">
                <div>
                  <label htmlFor="ticket-status-select">Status</label>
                  <select
                    id="ticket-status-select"
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    disabled={updating}
                    className="filter-select"
                  >
                    {ticketStatuses.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex-1">
                  <label htmlFor="ticket-comment-input">Resolution Comment</label>
                  <input
                    id="ticket-comment-input"
                    type="text"
                    placeholder="Add an update note or resolution reason…"
                    value={statusComment}
                    onChange={(e) => setStatusComment(e.target.value)}
                    disabled={updating}
                  />
                </div>
                <div className="btn-align-end">
                  <button
                    type="button"
                    className="primary-button small-btn"
                    onClick={handleUpdateStatus}
                    disabled={updating || selectedStatus === ticket.status}
                  >
                    {updating ? 'Updating…' : 'Update Status'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </section>
    </div>
  )
}
