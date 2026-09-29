import { useCallback, useEffect, useState } from 'react'
import {
  ArrowUpRight, CheckCircle2, ChevronRight, CircleAlert,
  LayoutDashboard, LogOut, MessageSquareText, Package,
  RefreshCw, Ticket, Utensils, X,
} from 'lucide-react'
import {
  agentApi, api, apiConfigured, dashboardApi, getApiErrorMessage, ticketsApi,
} from './api.js'
import './App.css'

import Overview from './components/Overview.jsx'
import OrdersView from './components/OrdersView.jsx'
import TicketsView from './components/TicketsView.jsx'
import AssistantView from './components/AssistantView.jsx'
import OrderDetailModal from './components/OrderDetailModal.jsx'
import TicketDetailModal from './components/TicketDetailModal.jsx'
import TicketCreateModal from './components/TicketCreateModal.jsx'
import ExecutionModal from './components/ExecutionModal.jsx'
import CustomersModal from './components/CustomersModal.jsx'

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('dineassist_token'))
  const [profile, setProfile] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginPending, setLoginPending] = useState(false)

  // Navigation & View Filter States
  const [activeView, setActiveView] = useState('overview')
  const [viewFilters, setViewFilters] = useState({})

  // Workspace Data
  const [summary, setSummary] = useState(null)
  const [activity, setActivity] = useState(null)
  const [recentTickets, setRecentTickets] = useState([])
  const [loading, setLoading] = useState(false)
  const [dataError, setDataError] = useState('')

  // Assistant State
  const [assistantStatus, setAssistantStatus] = useState('Ready')
  const [chatInput, setChatInput] = useState('')
  const [chatPending, setChatPending] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content:
        'Welcome to DineAssist Restaurant Operations Copilot. How can I help you today with live orders, ticket triage, or store policies?',
    },
  ])
  const [conversationId, setConversationId] = useState(null)

  // Modals
  const [activeOrderId, setActiveOrderId] = useState(null)
  const [activeTicketId, setActiveTicketId] = useState(null)
  const [activeExecutionId, setActiveExecutionId] = useState(null)
  const [customersModalOpen, setCustomersModalOpen] = useState(false)
  const [ticketCreateModalOpen, setTicketCreateModalOpen] = useState(false)

  // Notification Toast
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev))
    }, 4000)
  }

  const logout = () => {
    localStorage.removeItem('dineassist_token')
    setToken(null)
    setProfile(null)
    setActiveView('overview')
  }

  const loadData = useCallback(async () => {
    if (!localStorage.getItem('dineassist_token')) return false
    try {
      const [summaryRes, activityRes, ticketsRes] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getActivity(),
        ticketsApi.list({ per_page: 5 }),
      ])
      setSummary(summaryRes.data)
      setActivity(activityRes.data)
      setRecentTickets(ticketsRes.data.items || [])
      setDataError('')
      return true
    } catch (error) {
      setDataError(getApiErrorMessage(error))
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const refreshData = () => {
    setLoading(true)
    void loadData()
  }

  const handleNavigate = (view, filters = {}) => {
    setViewFilters(filters)
    setActiveView(view)
  }

  const checkAssistantStatus = async () => {
    try {
      const { data } = await api.get('/health/ready')
      setAssistantStatus(data.ai_provider ? `${data.ai_provider} active` : 'Active')
    } catch {
      setAssistantStatus('Operational')
    }
  }

  // Check login & load initial data
  useEffect(() => {
    const onUnauthorized = () => logout()
    window.addEventListener('dineassist:unauthorized', onUnauthorized)
    return () => window.removeEventListener('dineassist:unauthorized', onUnauthorized)
  }, [])

  useEffect(() => {
    if (!token) return undefined
    let cancelled = false

    api
      .get('/api/auth/me')
      .then(({ data }) => {
        if (!cancelled) setProfile(data)
      })
      .catch(() => {
        if (!cancelled) logout()
      })

    void loadData()
    void checkAssistantStatus()

    return () => {
      cancelled = true
    }
  }, [token, loadData])

  async function login(event) {
    event.preventDefault()
    setLoginError('')
    setLoginPending(true)
    try {
      const { data } = await api.post('/api/auth/login', { email, password })
      localStorage.setItem('dineassist_token', data.access_token)
      setToken(data.access_token)
    } catch (error) {
      setLoginError(
        error.response?.status === 401
          ? 'Sign-in failed. Check your restaurant credentials and try again.'
          : getApiErrorMessage(error)
      )
    } finally {
      setLoginPending(false)
    }
  }

  async function sendMessage(event) {
    if (event) event.preventDefault()
    const message = chatInput.trim()
    if (!message || chatPending) return
    setChatPending(true)
    setChatMessages((current) => [...current, { role: 'user', content: message }])
    setChatInput('')

    try {
      const { data } = await agentApi.chat({
        message,
        conversation_id: conversationId,
      })
      setConversationId(data.conversation_id)
      setChatMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: data.message,
          sources: data.sources || [],
          tools: data.tool_calls || [],
          isFallback: data.is_fallback,
        },
      ])
    } catch (error) {
      setChatMessages((current) => [
        ...current,
        {
          role: 'error',
          content: getApiErrorMessage(error),
        },
      ])
      setChatInput(message)
    } finally {
      setChatPending(false)
    }
  }

  const handleCreateTicket = async (formData) => {
    try {
      const { data } = await ticketsApi.create(formData)
      setTicketCreateModalOpen(false)
      showToast(`Support ticket ${data.ticket_id} created successfully!`)
      await loadData()
      return ''
    } catch (err) {
      return getApiErrorMessage(err)
    }
  }

  if (!token) {
    return (
      <LoginScreen
        email={email}
        password={password}
        error={loginError}
        pending={loginPending}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={login}
      />
    )
  }

  const navItems = [
    ['overview', LayoutDashboard, 'Overview'],
    ['orders', Package, 'Orders'],
    ['tickets', Ticket, 'Support tickets'],
    ['assistant', MessageSquareText, 'AI assistant'],
  ]

  const pageTitles = {
    overview: 'Operations Overview',
    orders: 'Order Operations',
    tickets: 'Support Tickets Queue',
    assistant: 'AI Support Assistant',
  }

  return (
    <div className="app-shell">
      {/* ─── SIDEBAR NAVIGATION ─────────────────────────────────────── */}
      <aside className="sidebar">
        <a
          className="brand"
          href="#overview"
          onClick={(e) => {
            e.preventDefault()
            handleNavigate('overview')
          }}
          aria-label="DineAssist overview"
        >
          <span className="brand-mark">
            <Utensils size={18} />
          </span>
          <span>
            DineAssist<small>RESTAURANT OPERATIONS</small>
          </span>
        </a>

        <div className="sidebar-label">Operations Console</div>
        <nav aria-label="Workspace navigation">
          {navItems.map(([id, Icon, label]) => (
            <button
              key={id}
              className={`nav-item${activeView === id ? ' active' : ''}`}
              onClick={() => handleNavigate(id)}
              aria-current={activeView === id ? 'page' : undefined}
            >
              <Icon size={18} />
              <span>{label}</span>
              {id === 'tickets' && summary?.open_tickets > 0 && (
                <b className="nav-badge">{summary.open_tickets}</b>
              )}
              {id === 'orders' && summary?.pending_orders > 0 && (
                <span className="nav-sub-badge">{summary.pending_orders}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="service-status">
            <span className="status-light" />
            <span>
              <strong>AI Copilot</strong>
              <small>{assistantStatus}</small>
            </span>
          </div>
          <button className="nav-item sign-out" onClick={logout}>
            <LogOut size={18} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* ─── MAIN CONTENT ───────────────────────────────────────────── */}
      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              <span>Workspace</span>
              <ChevronRight size={13} />
              <span>{pageTitles[activeView]}</span>
            </div>
            <h1>{pageTitles[activeView]}</h1>
          </div>
          <div className="top-actions">
            <button
              className="icon-button"
              title="Refresh workspace records"
              aria-label="Refresh workspace records"
              onClick={refreshData}
              disabled={loading}
            >
              <RefreshCw size={17} className={loading ? 'spin' : ''} />
            </button>
            <div className="profile">
              <div className="avatar">{profile?.name?.slice(0, 1) || 'A'}</div>
              <span>
                {profile?.name || 'Administrator'}
                <small>{profile?.role || 'Operations Lead'}</small>
              </span>
            </div>
          </div>
        </header>

        {!apiConfigured && (
          <div className="notice warning">
            <CircleAlert size={17} />
            <span>
              Backend URL is not configured. Set <code>VITE_API_BASE_URL</code> when building.
            </span>
          </div>
        )}

        {dataError && (
          <div className="notice error-notice" role="alert">
            <CircleAlert size={17} />
            <span>{dataError}</span>
            <button className="text-button" onClick={refreshData}>
              Try again
            </button>
          </div>
        )}

        {/* ─── ACTIVE VIEW RENDER ────────────────────────────────────── */}
        {activeView === 'overview' && (
          <Overview
            summary={summary}
            activity={activity}
            tickets={recentTickets}
            onNavigate={handleNavigate}
            onOpenOrder={(orderId) => setActiveOrderId(orderId)}
            onOpenTicket={(ticketId) => setActiveTicketId(ticketId)}
            onOpenExecution={(execId) => setActiveExecutionId(execId)}
            onOpenCustomers={() => setCustomersModalOpen(true)}
            onOpenCreateTicket={() => setTicketCreateModalOpen(true)}
            onRefresh={refreshData}
            loading={loading}
          />
        )}

        {activeView === 'orders' && (
          <OrdersView
            initialStatus={viewFilters.status || 'All statuses'}
            initialSearch={viewFilters.search || ''}
            onViewOrder={(orderId) => setActiveOrderId(orderId)}
          />
        )}

        {activeView === 'tickets' && (
          <TicketsView
            initialStatus={viewFilters.status || 'All statuses'}
            initialPriority={viewFilters.priority || 'All priorities'}
            initialCategory={viewFilters.category || 'All categories'}
            initialSearch={viewFilters.search || ''}
            onViewTicket={(ticketId) => setActiveTicketId(ticketId)}
            onCreateTicket={() => setTicketCreateModalOpen(true)}
          />
        )}

        {activeView === 'assistant' && (
          <AssistantView
            messages={chatMessages}
            input={chatInput}
            pending={chatPending}
            status={assistantStatus}
            profile={profile}
            onInput={setChatInput}
            onSubmit={sendMessage}
          />
        )}
      </main>

      {/* ─── POPUP MODALS ────────────────────────────────────────────── */}
      {activeOrderId && (
        <OrderDetailModal
          orderId={activeOrderId}
          onClose={() => setActiveOrderId(null)}
          onStatusUpdated={() => {
            void loadData()
          }}
        />
      )}

      {activeTicketId && (
        <TicketDetailModal
          ticketId={activeTicketId}
          onClose={() => setActiveTicketId(null)}
          onStatusUpdated={() => {
            void loadData()
          }}
          onOpenOrder={(orderRef) => {
            setActiveTicketId(null)
            setActiveOrderId(orderRef)
          }}
        />
      )}

      {activeExecutionId && (
        <ExecutionModal
          executionId={activeExecutionId}
          onClose={() => setActiveExecutionId(null)}
          onOpenTicket={(ticketId) => {
            setActiveExecutionId(null)
            setActiveTicketId(ticketId)
          }}
          onOpenOrder={(orderRef) => {
            setActiveExecutionId(null)
            setActiveOrderId(orderRef)
          }}
        />
      )}

      {customersModalOpen && (
        <CustomersModal
          totalCustomers={summary?.total_customers}
          totalConversations={summary?.total_conversations}
          onClose={() => setCustomersModalOpen(false)}
          onSelectConversation={(sessionId) => {
            setCustomersModalOpen(false)
            setConversationId(sessionId)
            handleNavigate('assistant')
          }}
        />
      )}

      {ticketCreateModalOpen && (
        <TicketCreateModal
          onClose={() => setTicketCreateModalOpen(false)}
          onSubmit={handleCreateTicket}
        />
      )}

      {/* ─── TOAST FEEDBACK ──────────────────────────────────────────── */}
      {toast && (
        <div
          className={`toast ${toast.type === 'error' ? 'error-toast' : ''}`}
          role={toast.type === 'error' ? 'alert' : 'status'}
        >
          {toast.type === 'error' ? <CircleAlert size={17} /> : <CheckCircle2 size={17} />}
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} aria-label="Dismiss notification">
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  )
}

function LoginScreen({
  email,
  password,
  error,
  pending,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}) {
  return (
    <main className="login-shell">
      <section className="login-art" aria-label="DineAssist restaurant operations">
        <div className="login-brand">
          <span className="brand-mark">
            <Utensils size={18} />
          </span>
          DineAssist
        </div>
        <div className="login-copy">
          <div className="eyebrow">Restaurant Operations Console</div>
          <h1>
            Every service detail,
            <br />
            <em>in good hands.</em>
          </h1>
          <p>
            Real-time orders, automated complaint triage, and AI customer care in one synchronized workspace.
          </p>
        </div>
        <div className="login-foot">
          <span className="status-light" /> Production Operations Workspace
        </div>
      </section>

      <form className="login-card" onSubmit={onSubmit}>
        <div className="eyebrow">Secure Sign In</div>
        <h2>Welcome Back</h2>
        <p className="muted">Sign in with your restaurant operations account.</p>

        <label htmlFor="login-email">Email Address</label>
        <input
          id="login-email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => onEmailChange(e.target.value)}
          placeholder="admin@restaurant.ai"
          required
        />

        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          placeholder="••••••••••••"
          minLength={6}
          maxLength={128}
          required
        />

        {error && (
          <div className="error-message" role="alert">
            <CircleAlert size={16} />
            {error}
          </div>
        )}

        <button className="primary-button" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in to Console'}
          {!pending && <ArrowUpRight size={17} />}
        </button>

        {!apiConfigured && (
          <div className="config-hint">
            This static build has no backend URL configured. Set <code>VITE_API_BASE_URL</code> and rebuild.
          </div>
        )}
      </form>
    </main>
  )
}