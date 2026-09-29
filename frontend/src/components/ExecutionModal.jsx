import { useEffect, useState } from 'react'
import {
  Activity, CheckCircle2, ChevronRight, CircleAlert, Clock3, ExternalLink,
  Package, RefreshCw, Ticket, X,
} from 'lucide-react'
import { automationApi, getApiErrorMessage } from '../api.js'

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

export default function ExecutionModal({
  executionId,
  onClose,
  onOpenTicket,
  onOpenOrder,
}) {
  const [execution, setExecution] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    automationApi
      .getExecution(executionId)
      .then(({ data }) => {
        if (!cancelled) setExecution(data)
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
  }, [executionId])

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
        className="modal record-modal execution-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="execution-detail-title"
      >
        <div className="modal-heading">
          <div>
            <div className="breadcrumb modal-breadcrumb">
              <span>Automations</span>
              <ChevronRight size={13} />
              <span>{executionId.slice(0, 8)}</span>
            </div>
            <h2 id="execution-detail-title">Complaint Workflow Execution</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close workflow execution details"
          >
            <X size={18} />
          </button>
        </div>

        {loading && (
          <div className="modal-loading">
            <RefreshCw size={18} className="spin" />
            <span>Loading automation telemetry…</span>
          </div>
        )}

        {error && (
          <div className="notice error-notice" role="alert">
            <CircleAlert size={17} />
            <span>{error}</span>
          </div>
        )}

        {execution && (
          <div className="record-details execution-details-content">
            <div className="detail-meta-grid">
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Activity size={14} /> Workflow Status
                </span>
                <span className={`execution-state ${execution.status}`}>
                  {execution.status}
                </span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">Category</span>
                <strong className="meta-value">{execution.category || 'Unclassified'}</strong>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">Sentiment</span>
                <span className={`tag ${execution.sentiment?.toLowerCase() || 'medium'}`}>
                  {execution.sentiment || 'Neutral'}
                </span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">Urgency Score</span>
                <strong className="meta-value highlight">
                  {execution.urgency_score ? `${execution.urgency_score}/10` : 'N/A'}
                </strong>
              </div>
            </div>

            <div className="section-block">
              <h4 className="section-subtitle">Original Complaint Text</h4>
              <div className="complaint-quote">
                "{execution.complaint_text}"
              </div>
            </div>

            <div className="execution-links-strip">
              {execution.ticket_id && (
                <div className="link-badge-item">
                  <Ticket size={15} />
                  <span>Generated Ticket:</span>
                  <button
                    type="button"
                    className="link-inline"
                    onClick={() => onOpenTicket && onOpenTicket(execution.ticket_id)}
                  >
                    {execution.ticket_id} <ExternalLink size={12} />
                  </button>
                </div>
              )}
              {execution.order_reference && (
                <div className="link-badge-item">
                  <Package size={15} />
                  <span>Referenced Order:</span>
                  <button
                    type="button"
                    className="link-inline"
                    onClick={() => onOpenOrder && onOpenOrder(execution.order_reference)}
                  >
                    {execution.order_reference} <ExternalLink size={12} />
                  </button>
                </div>
              )}
              <div className="link-badge-item">
                <Clock3 size={15} />
                <span>Duration:</span>
                <strong>{execution.duration_ms ? `${execution.duration_ms}ms` : 'Fast'}</strong>
              </div>
              <div className="link-badge-item">
                <span>Executed:</span>
                <strong>{formatDate(execution.created_at)}</strong>
              </div>
            </div>

            {/* Workflow steps */}
            <div className="section-block">
              <h4 className="section-subtitle">Workflow Pipeline Steps</h4>
              {execution.workflow_steps && execution.workflow_steps.length > 0 ? (
                <div className="pipeline-steps">
                  {execution.workflow_steps.map((st, idx) => (
                    <div className="pipeline-step-card" key={idx}>
                      <div className="step-badge">
                        {st.status === 'completed' || st.status === 'success' ? (
                          <CheckCircle2 size={16} className="text-emerald" />
                        ) : (
                          <Activity size={16} />
                        )}
                        <span className="step-name">{st.step}</span>
                      </div>
                      <span className="step-detail">{st.detail}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-state">No pipeline step logs recorded.</p>
              )}
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
