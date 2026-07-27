import request from './request'

export function getDashboardStats() {
  return request.get('/dashboard/stats')
}

export function getDashboardTrend() {
  return request.get('/dashboard/trend')
}

export function getDashboardAdvice() {
  return request.get('/dashboard/advice', { timeout: 60000 })
}

export function exportDashboardExcel() {
  return request.get('/dashboard/export/excel', {
    responseType: 'blob',
    timeout: 60000,
  })
}

export function exportDashboardPdf() {
  return request.get('/dashboard/export/pdf', {
    responseType: 'blob',
    timeout: 60000,
  })
}
