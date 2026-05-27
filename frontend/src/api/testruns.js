import request from '@/utils/request'

export function getTestRuns(params) {
  return request.get('/testruns/', { params })
}

export function getTestRun(id) {
  return request.get(`/testruns/${id}/`)
}

export function createTestRun(data) {
  return request.post('/testruns/', data)
}

export function startTestRun(id) {
  return request.post(`/testruns/${id}/start/`)
}

export function completeTestRun(id) {
  return request.post(`/testruns/${id}/complete/`)
}

export function updateTestResult(runId, data) {
  return request.patch(`/testruns/${runId}/update_result/`, data)
}
