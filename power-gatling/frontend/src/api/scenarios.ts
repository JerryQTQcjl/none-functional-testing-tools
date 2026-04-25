import api from './client'

export interface Scenario {
  id: string
  name: string
  description: string
  target_url: string
  method: string
  headers: Record<string, string>
  body: string | null
  concurrent_users: number
  ramp_up_duration: number
  sustained_duration: number
  workers: number
  tags: string[]
  created_at: string
  updated_at: string
}

export const listScenarios = () => api.get('/scenarios').then(r => r.data || [])
export const getScenario = (id: string) => api.get(`/scenarios/${id}`).then(r => r.data)
export const createScenario = (data: Partial<Scenario>) => api.post('/scenarios', data).then(r => r.data)
export const updateScenario = (id: string, data: Partial<Scenario>) => api.put(`/scenarios/${id}`, data).then(r => r.data)
export const deleteScenario = (id: string) => api.delete(`/scenarios/${id}`).then(r => r.data)
export const getScenarioCode = (id: string) => api.get(`/scenarios/${id}/code`).then(r => r.data)
