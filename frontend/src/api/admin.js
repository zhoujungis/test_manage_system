import request from '@/utils/request'

export function getAdminPermissionBoard() {
  return request.get('/auth/admin/permissions/')
}

export function updateUserPermissions(userId, data) {
  return request.patch(`/auth/admin/users/${userId}/permissions/`, data)
}

export function createUser(data) {
  return request.post('/auth/admin/users/', data)
}

export function deleteUser(userId) {
  return request.delete(`/auth/admin/users/${userId}/`)
}

export function getUserList() {
  return request.get('/auth/users/')
}
