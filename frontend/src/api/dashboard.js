import request from '@/utils/request'

export function getDashboardStats(params) {
  return request.get('/dashboard/stats/', { params })
}
