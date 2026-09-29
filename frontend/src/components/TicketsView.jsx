import { useEffect, useState } from 'react'
import {
  CheckCircle2, CircleAlert, Eye, Plus,
  RefreshCw, Search, Ticket, X,
} from 'lucide-react'
import { ticketsApi, getApiErrorMessage } from '../api.js'

const ticketStatuses = ['All statuses', 'Open', 'In Progress', 'Resolved', 'Escalated']
const ticketPriorities = ['All priorities', 'Low', 'Medium', 'High']
const ticketCategories = [
  'All categories',
  'Payment',
  'Order',
  'Delivery',
  'Refund',
  'Technical',
  'Other',
]

const formatDate = (value) =>
  value
    ? new Date(value).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Not available'

export default function TicketsView({
  initialStatus = 'All statuses',
  initialPriority = 'All priorities',
  initialCategory = 'All categories',
  initialSearch = '',
  onViewTicket,
  onCreateTicket,
}) {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(initialSearch)
  const [statusFilter, setStatusFilter] = useState(initialStatus)
  const [priorityFilter, setPriorityFilter] = useState(initialPriority)
  const [categoryFilter, setCategoryFilter] = useState(initialCategory)
  const [updatingId, setUpdatingId] = useState(null)
  const [successToast, setSuccessToast] = useState('')

  const fetchTickets = async () => {
    setLoading(true)
    setError('')
    try {
      const params = { per_page: 100 }
      if (statusFilter && statusFilter !== 'All statuses') {
        params.status = statusFilter
      }
      if (priorityFilter && priorityFilter !== 'All priorities') {
        params.priority = priorityFilter
      }
      if (categoryFilter && categoryFilter !== 'All categories') {
        params.category = categoryFilter
      }
      if (search && search.trim()) {
        params.search = search.trim()
      }
      const { data } = await ticketsApi.list(params)
      setTickets(data.items || [])
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTickets()
    }, 250)
    return () => clearTimeout(timer)
  }, [statusFilter, priorityFilter, categoryFilter, search])

  const handleStatusChange = async (ticket, newStatus) => {
    if (!newStatus || newStatus === ticket.status) return
    setUpdatingId(ticket.ticket_id)
    setSuccessToast('')
    try {
      const { data } = await ticketsApi.updateStatus(ticket.ticket_id, {
        status: newStatus,
        comment: `Status modified directly in the ticket queue to ${newStatus}.`,
      })
      setTickets((prev) =>
        prev.map((t) => (t.ticket_id === ticket.ticket_id ? { ...t, status: data.status } : t))
      )
      setSuccessToast(`Ticket ${ticket.ticket_id} updated to "${newStatus}"`)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setUpdatingId(null)
    }
  }

  const clearFilters = () => {
    setSearch('')
    setStatusFilter('All statuses')
    setPriorityFilter('All priorities')
    setCategoryFilter('All categories')
  }

  const isFiltered =
    search.trim() !== '' ||
    statusFilter !== 'All statuses' ||
    priorityFilter !== 'All priorities' ||
    categoryFilter !== 'All categories'

  return (
    <section className="panel table-panel tickets-view-panel">
      <div className="panel-heading table-heading">
        <div>
          <div className="eyebrow">Customer Care Operations</div>
          <h2>Support Ticket Queue</h2>
          <p>
            {loading ? 'Fetching tickets…' : `${tickets.length} tickets in current view`}
          </p>
        </div>

        <div className="table-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={onCreateTicket}
          >
            <Plus size={16} /> New ticket
          </button>

          {/* Status Filter */}
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter tickets by status"
          >
            {ticketStatuses.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>

          {/* Priority Filter */}
          <select
            className="filter-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            aria-label="Filter tickets by priority"
          >
            {ticketPriorities.map((pr) => (
              <option key={pr} value={pr}>
                {pr}
              </option>
            ))}
          </select>

          {/* Category Filter */}
          <select
            className="filter-select"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            aria-label="Filter tickets by category"
          >
            {ticketCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          {/* Search Box */}
          <label className="search-field">
            <Search size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tickets, customers…"
              aria-label="Search tickets"
            />
            {search && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearch('')}
                title="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </label>

          {isFiltered && (
            <button
              type="button"
              className="secondary-button small-btn"
              onClick={clearFilters}
              title="Reset all filters"
            >
              Reset Filters
            </button>
          )}

          <button
            type="button"
            className="icon-button"
            onClick={fetchTickets}
            disabled={loading}
            title="Reload tickets"
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className="notice error-notice" role="alert">
          <CircleAlert size={17} />
          <span>{error}</span>
          <button type="button" className="text-button" onClick={fetchTickets}>
            Retry
          </button>
        </div>
      )}

      {successToast && (
        <div className="notice success-notice" role="status">
          <CheckCircle2 size={17} />
          <span>{successToast}</span>
          <button
            type="button"
            className="clear-search-btn"
            onClick={() => setSuccessToast('')}
          >
            <X size={14} />
          </button>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticket Details</th>
              <th>Customer</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created Time</th>
              <th>Quick Status</th>
              <th className="num-col">Action</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((row) => (
              <tr key={row.ticket_id} className="interactive-tr">
                <td>
                  <button
                    type="button"
                    className="record-link text-left"
                    onClick={() => onViewTicket(row.ticket_id)}
                  >
                    <strong>{row.ticket_id}</strong>
                    <small className="cell-subtitle">{row.title}</small>
                  </button>
                </td>
                <td>
                  <span className="customer-cell-name">
                    {row.customer_name || 'Guest'}
                  </span>
                </td>
                <td>
                  <span className="category-tag-cell">{row.category}</span>
                </td>
                <td>
                  <span className={`tag ${row.priority.toLowerCase()}`}>
                    {row.priority}
                  </span>
                </td>
                <td>
                  <span
                    className={`ticket-status ${row.status
                      .toLowerCase()
                      .replaceAll(' ', '-')}`}
                  >
                    {row.status}
                  </span>
                </td>
                <td>
                  <span className="date-cell">{formatDate(row.created_at)}</span>
                </td>
                <td className="status-action-cell">
                  <select
                    className="inline-status-select"
                    value={row.status}
                    onChange={(e) => handleStatusChange(row, e.target.value)}
                    disabled={updatingId === row.ticket_id}
                    aria-label={`Update status for ${row.ticket_id}`}
                  >
                    {ticketStatuses
                      .filter((s) => s !== 'All statuses')
                      .map((st) => (
                        <option key={st} value={st}>
                          {st}
                        </option>
                      ))}
                  </select>
                </td>
                <td className="num-col">
                  <button
                    type="button"
                    className="row-action"
                    onClick={() => onViewTicket(row.ticket_id)}
                    title={`View ticket ${row.ticket_id}`}
                    aria-label={`View ticket ${row.ticket_id}`}
                  >
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {tickets.length === 0 && !loading && (
          <div className="empty-state">
            <Ticket size={28} className="empty-icon" />
            <p>
              {isFiltered
                ? 'No tickets match your filter criteria.'
                : 'No support tickets found in the database.'}
            </p>
            {isFiltered && (
              <button
                type="button"
                className="secondary-button small-btn mt-2"
                onClick={clearFilters}
              >
                Clear all filters
              </button>
            )}
          </div>
        )}

        {loading && tickets.length === 0 && (
          <div className="table-loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Retrieving support tickets…</span>
          </div>
        )}
      </div>
    </section>
  )
}
