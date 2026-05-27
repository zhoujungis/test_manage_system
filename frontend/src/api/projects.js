import request from '@/utils/request'

export function getProjects(params) {
  return request.get('/projects/', { params })
}

export function getProject(id) {
  return request.get(`/projects/${id}/`)
}

export function createProject(data) {
  return request.post('/projects/', data)
}

export function updateProject(id, data) {
  return request.put(`/projects/${id}/`, data)
}

export function deleteProject(id) {
  return request.delete(`/projects/${id}/`)
}

export function getModules(projectId) {
  return request.get(`/projects/${projectId}/modules/`)
}

export function getAllModules() {
  return request.get('/modules/')
}

export function createModule(projectId, data) {
  return request.post(`/projects/${projectId}/add_module/`, data)
}

export function updateModule(id, data) {
  return request.put(`/modules/${id}/`, data)
}

export function deleteModule(id) {
  return request.delete(`/modules/${id}/`)
}

// Project Members
export function getMembers(projectId) {
  return request.get(`/projects/${projectId}/members/`)
}
export function addMember(projectId, data) {
  return request.post(`/projects/${projectId}/members/`, data)
}
export function removeMember(id) {
  return request.delete(`/project-members/${id}/`)
}

// Project Tasks
export function getTasks(projectId) {
  return request.get(`/projects/${projectId}/tasks/`)
}
export function createTask(projectId, data) {
  return request.post(`/projects/${projectId}/tasks/`, data)
}
export function updateTask(id, data) {
  return request.patch(`/project-tasks/${id}/`, data)
}
export function deleteTask(id) {
  return request.delete(`/project-tasks/${id}/`)
}

// Test Case Assignments
export function getCaseAssignments(projectId, params) {
  return request.get(`/projects/${projectId}/case_assignments/`, { params })
}
export function createCaseAssignment(projectId, data) {
  return request.post(`/projects/${projectId}/case_assignments/`, data)
}
export function getCaseAssignment(id) {
  return request.get(`/case-assignments/${id}/`)
}

export function updateCaseAssignment(id, data) {
  return request.patch(`/case-assignments/${id}/`, data)
}

export function uploadAssignmentAttachment(assignmentId, file) {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/case-assignments/${assignmentId}/attachments/`, form, {
    timeout: 120000,
  })
}

export function deleteAssignmentAttachment(assignmentId, attachmentId) {
  return request.delete(`/case-assignments/${assignmentId}/attachments/${attachmentId}/`)
}
export function deleteCaseAssignment(id) {
  return request.delete(`/case-assignments/${id}/`)
}

export function getLibraryModules(productLine) {
  return request.get('/library-modules/', { params: { product_line: productLine } })
}

export function createLibraryModule(data) {
  return request.post('/library-modules/', data)
}

export function batchApprove(projectId, ids) {
  return request.post(`/projects/${projectId}/batch_approve/`, { ids })
}
