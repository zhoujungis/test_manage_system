import request from '@/utils/request'

export function getDefects(params) {
  return request.get('/defects/', { params })
}

export function getDefect(id) {
  return request.get(`/defects/${id}/`)
}

export function createDefect(data) {
  return request.post('/defects/', data)
}

export function updateDefect(id, data) {
  return request.put(`/defects/${id}/`, data)
}

export function deleteDefect(id) {
  return request.delete(`/defects/${id}/`)
}
