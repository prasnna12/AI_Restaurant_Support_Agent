import { useEffect, useState } from 'react'
import {
  CheckCircle2, CircleAlert, Eye,
  Filter, Package, RefreshCw, Search, X,
} from 'lucide-react'
import { ordersApi, getApiErrorMessage } from '../api.js'

const orderStatusList = [
  'All statuses',
  'pending',
  'confirmed',
  'preparing',
  'out_for_delivery',
  'delivered',
  'cancelled',
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

export default function OrdersView({
  initialStatus = 'All statuses',
  initialSearch = '',
  onViewOrder,
}) {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(initialSearch)
  const [statusFilter, setStatusFilter] = useState(initialStatus)
  const [updatingId, setUpdatingId] = useState(null)
  const [successToast, setSuccessToast] = useState('')

  const fetchOrders = async (currentStatus, currentSearch) => {
    setLoading(true)
    setError('')
    try {
      const params = { per_page: 100 }
      if (currentStatus && currentStatus !== 'All statuses') {
        params.status = currentStatus
      }
      if (currentSearch && currentSearch.trim()) {
        params.search = currentSearch.trim()
      }
      const { data } = await ordersApi.list(params)
      setOrders(data.items || [])
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchOrders(statusFilter, search)
    }, 250)
    return () => clearTimeout(timer)
  }, [statusFilter, search])

  const handleStatusChange = async (orderId, newStatus) => {
    if (!newStatus) return
    setUpdatingId(orderId)
    setSuccessToast('')
    try {
      const { data } = await ordersApi.updateStatus(orderId, newStatus)
      setOrders((prev) =>
        prev.map((o) => (o.order_id === orderId ? { ...o, status: data.status } : o))
      )
      setSuccessToast(`Order ${orderId} updated to "${newStatus.replaceAll('_', ' ')}"`)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setUpdatingId(null)
    }
  }

  const clearFilters = () => {
    setSearch('')
    setStatusFilter('All statuses')
  }

  const isFiltered = search.trim() !== '' || statusFilter !== 'All statuses'

  return (
    <section className="panel table-panel orders-view-panel">
      <div className="panel-heading table-heading">
        <div>
          <div className="eyebrow">Kitchen & Delivery Logistics</div>
          <h2>Live Order Operations</h2>
          <p>
            {loading ? 'Fetching orders…' : `${orders.length} orders retrieved from database`}
          </p>
        </div>

        <div className="table-actions">
          {/* Status Filter */}
          <div className="filter-group">
            <Filter size={15} className="filter-icon" />
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter orders by status"
            >
              {orderStatusList.map((st) => (
                <option key={st} value={st}>
                  {st === 'All statuses' ? 'All statuses' : st.replaceAll('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Search Box */}
          <label className="search-field">
            <Search size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Order ID or Customer…"
              aria-label="Search orders"
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
              title="Reset search and filters"
            >
              Reset Filters
            </button>
          )}

          <button
            type="button"
            className="icon-button"
            onClick={() => fetchOrders(statusFilter, search)}
            disabled={loading}
            title="Reload orders"
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className="notice error-notice" role="alert">
          <CircleAlert size={17} />
          <span>{error}</span>
          <button
            type="button"
            className="text-button"
            onClick={() => fetchOrders(statusFilter, search)}
          >
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
              <th>Order ID</th>
              <th>Customer</th>
              <th>Status</th>
              <th>Total Amount</th>
              <th>Placed Time</th>
              <th>Quick Status</th>
              <th className="num-col">Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.order_id} className="interactive-tr">
                <td>
                  <button
                    type="button"
                    className="record-link text-left"
                    onClick={() => onViewOrder(order.order_id)}
                  >
                    <strong>{order.order_id}</strong>
                    <small className="cell-subtitle">{order.item_count} items</small>
                  </button>
                </td>
                <td>
                  <span className="customer-cell-name">
                    {order.customer_name || 'Walk-in Guest'}
                  </span>
                </td>
                <td>
                  <span className={`status-pill ${order.status}`}>
                    <i />
                    {order.status.replaceAll('_', ' ')}
                  </span>
                </td>
                <td>
                  <strong className="order-price-cell">
                    ${Number(order.grand_total).toFixed(2)}
                  </strong>
                </td>
                <td>
                  <span className="date-cell">{formatDate(order.created_at)}</span>
                </td>
                <td className="status-action-cell">
                  <select
                    className="inline-status-select"
                    value={order.status}
                    onChange={(e) => handleStatusChange(order.order_id, e.target.value)}
                    disabled={updatingId === order.order_id}
                    aria-label={`Update status for ${order.order_id}`}
                  >
                    {orderStatusList
                      .filter((s) => s !== 'All statuses')
                      .map((st) => (
                        <option key={st} value={st}>
                          {st.replaceAll('_', ' ')}
                        </option>
                      ))}
                  </select>
                </td>
                <td className="num-col">
                  <button
                    type="button"
                    className="row-action"
                    onClick={() => onViewOrder(order.order_id)}
                    title={`View order ${order.order_id}`}
                    aria-label={`View order ${order.order_id}`}
                  >
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {orders.length === 0 && !loading && (
          <div className="empty-state">
            <Package size={28} className="empty-icon" />
            <p>
              {isFiltered
                ? 'No orders match your filter criteria.'
                : 'No order records found in the database.'}
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

        {loading && orders.length === 0 && (
          <div className="table-loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Retrieving restaurant orders…</span>
          </div>
        )}
      </div>
    </section>
  )
}
