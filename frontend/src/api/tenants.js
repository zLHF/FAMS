import http from './index'

export function getTenants(params) { return http.get('/tenants', { params }) }
export function createTenant(data) { return http.post('/tenants', data) }
export function updateTenant(id, data) { return http.put(`/tenants/${id}`, data) }
export function deleteTenant(id) { return http.delete(`/tenants/${id}`) }
export function getTenantMembers(id) { return http.get(`/tenants/${id}/members`) }
