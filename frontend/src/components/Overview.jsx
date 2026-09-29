import { lazy, Suspense } from 'react'
import {
  Activity, ArrowRight, ChevronRight, Clock3,
  MessageSquareText, Package, Plus, RefreshCw, Search,
  ShieldCheck, Tag, Ticket, Users,
} from 'lucide-react'

const SupportVolumeChart = lazy(() => import('../SupportVolumeChart.jsx'))

const formatDate = (value) =>
  value
    ? new Date(value).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Not available'

export default function Overview({
  summary,
  activity,
  tickets,
  onNavigate,
  _onOpenOrder,
  onOpenTicket,
  onOpenExecution,
  onOpenCustomers,
  onOpenCreateTicket,
  onRefresh,
  loading,
}) {
  const hasSampleData = summary?.sample_data_notice?.toLowerCase().includes('sample') ||
    activity?.sample_data_notice?.toLowerCase().includes('sample')

  const categoryEntries = summary?.category_distribution
    ? Object.entries(summary.category_distribution)
    : []

  return (
    <div className="overview-page">
      {hasSampleData && (
        <div className="sample-note">
          <Activity size={15} />
          <span>Notice: Live workspace data seeded for restaurant operations.</span>
        </div>
      )}

      {/* ─── QUICK ACTIONS BAR ────────────────────────────────────────── */}
      <section className="quick-actions-bar" aria-label="Operational quick actions">
        <div className="quick-actions-left">
          <span className="quick-actions-label">Quick Actions:</span>
          <button
            type="button"
            className="quick-action-btn primary"
            onClick={onOpenCreateTicket}
          >
            <Plus size={15} />
            <span>New Ticket</span>
          </button>
          <button
            type="button"
            className="quick-action-btn"
            onClick={() => onNavigate('orders')}
          >
            <Search size={15} />
            <span>Order Lookup</span>
          </button>
          <button
            type="button"
            className="quick-action-btn"
            onClick={() => onNavigate('assistant')}
          >
            <MessageSquareText size={15} />
            <span>Ask AI Copilot</span>
          </button>
        </div>
        <div className="quick-actions-right">
          <button
            type="button"
            className="quick-action-btn subtle"
            onClick={onRefresh}
            disabled={loading}
            title="Refresh operations metrics"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>{loading ? 'Syncing…' : 'Sync Metrics'}</span>
          </button>
        </div>
      </section>

      {/* ─── INTERACTIVE METRICS CARDS ────────────────────────────────── */}
      <section className="metrics" aria-label="Operations summary cards">
        {/* 1. Orders Card */}
        <article
          className="metric clickable-card"
          tabIndex={0}
          role="button"
          onClick={() => onNavigate('orders')}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onNavigate('orders')
          }}
          aria-label="View all orders"
        >
          <div className="metric-header">
            <div className="metric-icon amber">
              <Package size={18} />
            </div>
            <span className="card-affordance">
              View <ArrowRight size={13} />
            </span>
          </div>
          <div className="metric-body">
            <span className="metric-label">Total Orders</span>
            <strong className="metric-value">{summary?.total_orders ?? '—'}</strong>
            <button
              type="button"
              className="metric-sub-link"
              onClick={(e) => {
                e.stopPropagation()
                onNavigate('orders', { status: 'preparing' })
              }}
              title="Filter in-progress orders"
            >
              <span>{summary?.pending_orders ?? 0} in progress</span>
              <ChevronRight size={12} />
            </button>
          </div>
        </article>

        {/* 2. Open Tickets Card */}
        <article
          className="metric clickable-card"
          tabIndex={0}
          role="button"
          onClick={() => onNavigate('tickets', { status: 'Open' })}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ')
              onNavigate('tickets', { status: 'Open' })
          }}
          aria-label="View open support tickets"
        >
          <div className="metric-header">
            <div className="metric-icon coral">
              <Ticket size={18} />
            </div>
            <span className="card-affordance">
              Filter <ArrowRight size={13} />
            </span>
          </div>
          <div className="metric-body">
            <span className="metric-label">Open Tickets</span>
            <strong className="metric-value">{summary?.open_tickets ?? '—'}</strong>
            <button
              type="button"
              className="metric-sub-link"
              onClick={(e) => {
                e.stopPropagation()
                onNavigate('tickets', { priority: 'High' })
              }}
              title="Filter high priority tickets"
            >
              <span>{summary?.high_priority_tickets ?? 0} high priority</span>
              <ChevronRight size={12} />
            </button>
          </div>
        </article>

        {/* 3. Customers Card */}
        <article
          className="metric clickable-card"
          tabIndex={0}
          role="button"
          onClick={onOpenCustomers}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onOpenCustomers()
          }}
          aria-label="View restaurant guests and conversation history"
        >
          <div className="metric-header">
            <div className="metric-icon teal">
              <Users size={18} />
            </div>
            <span className="card-affordance">
              Directory <ArrowRight size={13} />
            </span>
          </div>
          <div className="metric-body">
            <span className="metric-label">Registered Guests</span>
            <strong className="metric-value">{summary?.total_customers ?? '—'}</strong>
            <button
              type="button"
              className="metric-sub-link"
              onClick={(e) => {
                e.stopPropagation()
                onOpenCustomers()
              }}
              title="Open conversations list"
            >
              <span>{summary?.total_conversations ?? 0} AI chats</span>
              <ChevronRight size={12} />
            </button>
          </div>
        </article>

        {/* 4. Resolved Tickets Card */}
        <article
          className="metric clickable-card"
          tabIndex={0}
          role="button"
          onClick={() => onNavigate('tickets', { status: 'Resolved' })}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ')
              onNavigate('tickets', { status: 'Resolved' })
          }}
          aria-label="View resolved tickets"
        >
          <div className="metric-header">
            <div className="metric-icon green">
              <ShieldCheck size={18} />
            </div>
            <span className="card-affordance">
              Inspect <ArrowRight size={13} />
            </span>
          </div>
          <div className="metric-body">
            <span className="metric-label">Resolved Tickets</span>
            <strong className="metric-value">{summary?.resolved_tickets ?? '—'}</strong>
            <button
              type="button"
              className="metric-sub-link"
              onClick={(e) => {
                e.stopPropagation()
                onNavigate('tickets', { status: 'Escalated' })
              }}
              title="Filter escalated tickets"
            >
              <span>{summary?.escalated_tickets ?? 0} escalated</span>
              <ChevronRight size={12} />
            </button>
          </div>
        </article>
      </section>

      {/* ─── CATEGORY DISTRIBUTION STRIP ─────────────────────────────── */}
      {categoryEntries.length > 0 && (
        <section className="category-strip-panel" aria-label="Ticket category distribution">
          <div className="category-strip-header">
            <div className="strip-title-group">
              <Tag size={15} />
              <span>Ticket Categories:</span>
            </div>
            <small className="strip-hint">Click category to filter tickets</small>
          </div>
          <div className="category-badges-row">
            {categoryEntries.map(([category, count]) => (
              <button
                key={category}
                type="button"
                className="category-pill-btn"
                onClick={() => onNavigate('tickets', { category })}
                title={`Filter tickets by category: ${category}`}
              >
                <span className="pill-name">{category}</span>
                <span className="pill-count">{count}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ─── CHARTS & RECENT TICKETS GRID ────────────────────────────── */}
      <div className="dashboard-grid">
        {/* Support Volume Chart */}
        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h2>Support Volume</h2>
              <p>Tickets created over the past 7 days (click a date to filter)</p>
            </div>
            <div className="chart-legend-group">
              <span className="chart-key">
                <i /> Tickets Trend
              </span>
            </div>
          </div>
          <div className="chart-wrap">
            {activity?.chart_data?.length ? (
              <Suspense fallback={<div className="chart-loading">Loading chart…</div>}>
                <SupportVolumeChart
                  data={activity.chart_data}
                  onSelectDate={(_date) => {
                    // Navigate to tickets page
                    onNavigate('tickets')
                  }}
                />
              </Suspense>
            ) : (
              <div className="empty-state">Activity data is not available yet.</div>
            )}
          </div>
        </section>

        {/* Latest Tickets Panel */}
        <section className="panel recent-panel">
          <div className="panel-heading">
            <div>
              <h2>Latest Tickets</h2>
              <p>Newest items in the support queue</p>
            </div>
            <button
              type="button"
              className="text-button inline-flex-btn"
              onClick={() => onNavigate('tickets')}
            >
              <span>View all</span>
              <ChevronRight size={14} />
            </button>
          </div>

          {tickets.length ? (
            <ul className="recent-list">
              {tickets.map((ticket) => (
                <li key={ticket.ticket_id}>
                  <button
                    type="button"
                    className="recent-ticket clickable-row"
                    onClick={() => onOpenTicket(ticket.ticket_id)}
                    title={`Inspect details for ${ticket.ticket_id}`}
                  >
                    <span className="recent-ticket-main">
                      <strong>{ticket.title}</strong>
                      <small>
                        {ticket.ticket_id} · {ticket.customer_name || 'Guest'} ·{' '}
                        {formatDate(ticket.created_at)}
                      </small>
                    </span>
                    <div className="ticket-badges-group">
                      <span className={`tag ${ticket.priority.toLowerCase()}`}>
                        {ticket.priority}
                      </span>
                      <span
                        className={`ticket-status small ${ticket.status
                          .toLowerCase()
                          .replaceAll(' ', '-')}`}
                      >
                        {ticket.status}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">No support tickets are available.</div>
          )}
        </section>
      </div>

      {/* ─── RECENT COMPLAINT WORKFLOWS / AUTOMATION ──────────────────── */}
      {activity?.recent_executions && activity.recent_executions.length > 0 && (
        <section className="panel execution-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Complaint Automations</h2>
              <p>Automated triage executions returned by the service (click to inspect)</p>
            </div>
            <Clock3 size={18} className="heading-icon" />
          </div>
          <div className="execution-list">
            {activity.recent_executions.slice(0, 4).map((execution) => (
              <button
                key={execution.execution_id}
                type="button"
                className="execution-row clickable-exec-row"
                onClick={() => onOpenExecution(execution.execution_id)}
                title="View automation workflow details"
              >
                <span className={`execution-state ${execution.status}`}>
                  {execution.status}
                </span>
                <strong className="exec-category">
                  {execution.category || 'Unclassified'}
                </strong>
                <span className="exec-priority">
                  Priority: {execution.priority || 'Normal'}
                </span>
                <span className="exec-id-badge">
                  ID: {execution.short_id || execution.execution_id.slice(0, 8)}
                </span>
                <small className="exec-date">{formatDate(execution.created_at)}</small>
                <ChevronRight size={15} className="row-chevron" />
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ─── RECENT AI CONVERSATIONS PREVIEW ─────────────────────────── */}
      {activity?.recent_conversations && activity.recent_conversations.length > 0 && (
        <section className="panel conversations-overview-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Copilot Conversations</h2>
              <p>Active guest and operations AI support threads</p>
            </div>
            <button
              type="button"
              className="text-button inline-flex-btn"
              onClick={onOpenCustomers}
            >
              <span>All sessions</span>
              <ChevronRight size={14} />
            </button>
          </div>
          <div className="conversations-grid">
            {activity.recent_conversations.slice(0, 3).map((conv) => (
              <div
                key={conv.session_id}
                className="conversation-card-overview"
                role="button"
                tabIndex={0}
                onClick={() => onNavigate('assistant', { sessionId: conv.session_id })}
                onKeyDown={(e) => {
                  if (e.key === 'Enter')
                    onNavigate('assistant', { sessionId: conv.session_id })
                }}
              >
                <div className="conv-card-top">
                  <MessageSquareText size={16} className="text-teal" />
                  <span className="conv-time">{formatDate(conv.updated_at)}</span>
                </div>
                <strong className="conv-card-title">{conv.title || 'Support Query'}</strong>
                <div className="conv-card-foot">
                  <span>Session: {conv.short_id || conv.session_id.slice(0, 8)}</span>
                  <span className="action-hint">Resume →</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
