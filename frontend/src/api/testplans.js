import request from '@/utils/request'

export function getTestPlans(params) {
  return request.get('/testplans/', { params })
}

export function getTestPlan(id) {
  return request.get(`/testplans/${id}/`)
}

export function createTestPlan(data) {
  return request.post('/testplans/', data)
}

export function updateTestPlan(id, data) {
  return request.put(`/testplans/${id}/`, data)
}

export function deleteTestPlan(id) {
  return request.delete(`/testplans/${id}/`)
}

export function addCasesToPlan(planId, caseIds) {
  return request.post(`/testplans/${planId}/add_cases/`, { case_ids: caseIds })
}

export function removeCaseFromPlan(planId, caseId) {
  return request.delete(`/testplans/${planId}/remove_case/`, { data: { case_id: caseId } })
}
