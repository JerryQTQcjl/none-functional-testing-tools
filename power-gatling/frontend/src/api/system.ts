import api from './client'

export interface SystemStatus {
  redis_connected: boolean
  active_workers: number
  registered_workers: number
  active_executions: number
  workers: Array<{
    worker_id: string
    status: string
    execution_id: string | null
    last_heartbeat: string | null
  }>
}

export const getSystemStatus = () => api.get('/system/status').then(r => r.data) as Promise<SystemStatus>
export const getWorkers = () => api.get('/system/workers').then(r => r.data || [])
