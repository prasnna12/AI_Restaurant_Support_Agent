import { useEffect, useState } from 'react'
import { CircleAlert, Plus, X } from 'lucide-react'

const ticketCategories = ['Payment', 'Order', 'Delivery', 'Refund', 'Technical', 'Other']

export default function TicketCreateModal({ onClose, onSubmit }) {
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  async function submit(event) {
    event.preventDefault()
    setPending(true)
    setError('')
    const form = new FormData(event.currentTarget)
    const result = await onSubmit({
      title: form.get('title').trim(),
      description: form.get('description').trim(),
      category: form.get('category'),
      priority: form.get('priority'),
      order_reference: form.get('order_reference').trim() || null,
    })
    if (result) setError(result)
    setPending(false)
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="modal ticket-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-form-title"
      >
        <div className="modal-heading">
          <div>
            <div className="eyebrow">Support Queue</div>
            <h2 id="ticket-form-title">Create Support Ticket</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close ticket form"
          >
            <X size={18} />
          </button>
        </div>

        <form className="ticket-form" onSubmit={submit}>
          <label htmlFor="ticket-title">Ticket Subject / Title</label>
          <input
            id="ticket-title"
            name="title"
            placeholder="e.g. Missing extra sauces in delivery"
            minLength={5}
            maxLength={500}
            required
            autoFocus
          />

          <label htmlFor="ticket-description">Detailed Issue Description</label>
          <textarea
            id="ticket-description"
            name="description"
            placeholder="Describe the guest complaint or incident in detail…"
            minLength={10}
            maxLength={5000}
            rows={4}
            required
          />

          <div className="form-row">
            <div>
              <label htmlFor="ticket-category">Category</label>
              <select id="ticket-category" name="category" defaultValue="Order">
                {ticketCategories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="ticket-priority">Priority</label>
              <select id="ticket-priority" name="priority" defaultValue="Medium">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
          </div>

          <label htmlFor="ticket-order">
            Order Reference <span className="optional">(Optional)</span>
          </label>
          <input
            id="ticket-order"
            name="order_reference"
            placeholder="e.g. ORD-1001"
            pattern="ORD-[0-9]+"
            title="Use an order reference like ORD-1001"
            maxLength={20}
          />

          {error && (
            <div className="error-message" role="alert">
              <CircleAlert size={16} />
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={onClose}
              disabled={pending}
            >
              Cancel
            </button>
            <button className="primary-button" type="submit" disabled={pending}>
              {pending ? 'Submitting…' : 'Create Ticket'}
              {!pending && <Plus size={16} />}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
