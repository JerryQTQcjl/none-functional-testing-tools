import api from './client'

export interface Execution {
  id: string
  scenario_id: string
  scenario_name?: string
  status: string
  workers: number
  started_at: string | null
  ended_at: string | null
  total_requests: number
  total_errors: number
  mean_rt: number
  p50_rt: number
  p90_rt: number
  p95_rt: number
  p99_rt: number
  max_rt: number
  rps: number
  error_rate: number
}

export interface MetricPoint {
  timestamp: number
  rps: number
  mean_rt: number
  p50_rt: number
  p90_rt: number
  p99_rt: number
  error_rate: number
  active_users: number
  total_requests: number
  total_errors: number
}

export const startExecution = (scenario_id: string) => api.post('/executions', { scenario_id }).then(r => r.data)
export const listExecutions = () => api.get('/executions').then(r => r.data || [])
export const getExecution = (id: string) => api.get(`/executions/${id}`).then(r => r.data)
export const stopExecution = (id: string) => api.post(`/executions/${id}/stop`).then(r => r.data)
