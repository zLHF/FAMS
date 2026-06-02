import http from './index'
export function getRoles(params) { return http.get('/roles', { params }) }
export function createRole(data) { return http.post('/roles', data) }
export function updateRole(id, data) { return http.put(`/roles/${id}`, data) }
export function deleteRole(id) { return http.delete(`/roles/${id}`) }
export function assignPermissions(id, permission_ids) { return http.put(`/roles/${id}/permissions`, { permission_ids }) }
