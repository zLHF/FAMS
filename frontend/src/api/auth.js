import http from './index'
export function login(data) { return http.post('/auth/login', data) }
export function logout() { return http.post('/auth/logout') }
export function getMe() { return http.get('/auth/me') }
export function getTenants() { return http.get('/auth/tenants') }
export function switchTenant(tenantId) { return http.post('/auth/switch-tenant', { tenant_id: tenantId }) }
