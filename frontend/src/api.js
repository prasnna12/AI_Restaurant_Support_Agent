import axios from 'axios'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL
const baseURL = configuredBaseUrl || (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '')

export const apiConfigured = Boolean(baseURL)
export const api = axios.create({ baseURL, timeout: 15000 })

api.interceptors.request.use((config) => {
  if (!apiConfigured) {
    return Promise.reject(new Error('API_NOT_CONFIGURED'))
  }

  const token = localStorage.getItem('dineassist_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('dineassist_token')
      window.dispatchEvent(new Event('dineassist:unauthorized'))
    }
    return Promise.reject(error)
  }
)

export function getApiErrorMessage(error) {
  if (!error) return 'An unexpected error occurred.'
  if (error.message === 'API_NOT_CONFIGURED') {
    return 'The backend API URL is not configured for this deployment.'
  }
  if (error.code === 'ECONNABORTED') {
    return 'The request timed out. Please try again.'
  }
  if (!error.response) {
    return 'Could not reach the support service. Check the backend URL and try again.'
  }
  if (error.response.status >= 500) {
    return 'The support service encountered an error. Please try again shortly.'
  }
  if (error.response.data?.detail) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || d.message).join('; ')
    }
  }
  return 'The request could not be completed. Please try again.'
}

// ─── Service Methods ────────────────────────────────────────────────────────
export const ordersApi = {
  list: (params) => api.get('/api/orders', { params }),
  get: (orderId) => api.get(`/api/orders/${orderId}`),
  updateStatus: (orderId, status) => api.put(`/api/orders/${orderId}/status`, { status }),
}

export const ticketsApi = {
  list: (params) => api.get('/api/support/tickets', { params }),
  get: (ticketId) => api.get(`/api/support/tickets/${ticketId}`),
  create: (payload) => api.post('/api/support/tickets', payload),
  updateStatus: (ticketId, payload) => api.put(`/api/support/tickets/${ticketId}/status`, payload),
}

export const dashboardApi = {
  getSummary: () => api.get('/api/dashboard/summary'),
  getActivity: () => api.get('/api/dashboard/activity'),
}

export const automationApi = {
  listExecutions: (params) => api.get('/api/automation/executions', { params }),
  getExecution: (executionId) => api.get(`/api/automation/executions/${executionId}`),
  processComplaint: (payload) => api.post('/api/automation/complaints', payload),
}

export const agentApi = {
  chat: (payload) => api.post('/api/agent/chat', payload),
  listConversations: () => api.get('/api/agent/conversations'),
  getConversation: (sessionId) => api.get(`/api/agent/conversations/${sessionId}`),
}