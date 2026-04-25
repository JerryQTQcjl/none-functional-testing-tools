import api from './client'

export const getReportSummary = (id: string) => api.get(`/reports/${id}/summary`).then(r => r.data)
export const getReportTimeline = (id: string) => api.get(`/reports/${id}/timeline`).then(r => r.data || [])
