import { useEffect, useState } from 'react'
import {
  Calendar, CheckCircle2, ChevronRight, CircleAlert, DollarSign,
  Package, RefreshCw, User, Utensils, X,
} from 'lucide-react'
import { ordersApi, getApiErrorMessage } from '../api.js'

const orderStatusList = [
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
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Not available'

export default function OrderDetailModal({ orderId, onClose, onStatusUpdated }) {
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [updating, setUpdating] = useState(false)
  const [actionSuccess, setActionSuccess] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    ordersApi
      .get(orderId)
      .then(({ data }) => {
        if (!cancelled) {
          setOrder(data)
          setSelectedStatus(data.status)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getApiErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [orderId])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const handleUpdateStatus = async () => {
    if (!selectedStatus || selectedStatus === order?.status) return
    setUpdating(true)
    setActionSuccess('')
    setError('')

    try {
      const { data } = await ordersApi.updateStatus(order.order_id, selectedStatus)
      setOrder(data)
      setActionSuccess(`Status updated to "${data.status.replaceAll('_', ' ')}"`)
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
        className="modal record-modal order-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="order-detail-title"
      >
        <div className="modal-heading">
          <div>
            <div className="breadcrumb modal-breadcrumb">
              <span>Orders</span>
              <ChevronRight size={13} />
              <span>{orderId}</span>
            </div>
            <h2 id="order-detail-title">Order {orderId}</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close order details"
          >
            <X size={18} />
          </button>
        </div>

        {loading && (
          <div className="modal-loading">
            <RefreshCw size={18} className="spin" />
            <span>Loading order records from database…</span>
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

        {order && (
          <div className="record-details order-details-content">
            <div className="detail-meta-grid">
              <div className="detail-meta-card">
                <span className="meta-label">
                  <User size={14} /> Customer
                </span>
                <strong className="meta-value">{order.customer_name}</strong>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Package size={14} /> Status
                </span>
                <span className={`status-pill ${order.status}`}>
                  <i />
                  {order.status.replaceAll('_', ' ')}
                </span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <Calendar size={14} /> Placed
                </span>
                <span className="meta-value">{formatDate(order.created_at)}</span>
              </div>
              <div className="detail-meta-card">
                <span className="meta-label">
                  <DollarSign size={14} /> Total Amount
                </span>
                <strong className="meta-value highlight">
                  ${Number(order.grand_total).toFixed(2)}
                </strong>
              </div>
            </div>

            <div className="section-block">
              <h3 className="section-title">
                <Utensils size={16} /> Line Items ({order.items.length})
              </h3>
              <div className="items-table-wrap">
                <table className="items-table">
                  <thead>
                    <tr>
                      <th>Item Description</th>
                      <th className="num-col">Qty</th>
                      <th className="num-col">Unit Price</th>
                      <th className="num-col">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.items.map((item, idx) => (
                      <tr key={`${item.name}-${idx}`}>
                        <td>
                          <strong>{item.name}</strong>
                        </td>
                        <td className="num-col">{item.quantity}</td>
                        <td className="num-col">${Number(item.unit_price).toFixed(2)}</td>
                        <td className="num-col font-semibold">
                          ${Number(item.total_price).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="order-financials">
              <div className="financial-row">
                <span>Subtotal</span>
                <span>${Number(order.subtotal).toFixed(2)}</span>
              </div>
              <div className="financial-row">
                <span>Tax & Service</span>
                <span>${Number(order.tax).toFixed(2)}</span>
              </div>
              <div className="financial-row total-row">
                <strong>Grand Total</strong>
                <strong>${Number(order.grand_total).toFixed(2)}</strong>
              </div>
            </div>

            {order.notes && (
              <div className="order-notes-box">
                <strong>Special Kitchen / Delivery Notes:</strong>
                <p>{order.notes}</p>
              </div>
            )}

            {/* Status Update Control */}
            <div className="order-status-actions">
              <span className="action-label">Change Order Status:</span>
              <div className="status-form-group">
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  disabled={updating}
                  className="status-select-control"
                  aria-label="Select new order status"
                >
                  {orderStatusList.map((st) => (
                    <option key={st} value={st}>
                      {st.replaceAll('_', ' ')}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="primary-button small-btn"
                  onClick={handleUpdateStatus}
                  disabled={updating || selectedStatus === order.status}
                >
                  {updating ? 'Saving…' : 'Update Status'}
                </button>
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
