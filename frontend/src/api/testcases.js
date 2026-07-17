import request from '@/utils/request'

export function getTestCases(params) {
  return request.get('/testcases/', { params })
}

export function getTestCaseTree(params) {
  // 树视图专用：轻量投影，limit 上限 2000
  return request.get('/testcases-tree/', { params })
}

export function getTestCase(id) {
  return request.get(`/testcases/${id}/`)
}

export function createTestCase(data) {
  return request.post('/testcases/', data)
}

export function updateTestCase(id, data) {
  return request.patch(`/testcases/${id}/`, data)
}

export function deleteTestCase(id) {
  return request.delete(`/testcases/${id}/`)
}
