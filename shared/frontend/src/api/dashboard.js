import request from './request'

export function getDashboardStats() {
  return request.get('/dashboard/stats')
}

export function getDashboardTrend() {
  return request.get('/dashboard/trend')
}

export function getDashboardAdvice() {
  return request.get('/dashboard/advice')
}

export function exportDashboardExcel() {
  window.open('/api/dashboard/export/excel', '_blank')
}

export function exportDashboardPdf() {
  window.open('/api/dashboard/export/pdf', '_blank')
}
