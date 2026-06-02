import http from './index'
export function getPermissionTree() { return http.get('/permissions/tree') }
export function getRolePermissions(roleId) { return http.get(`/permissions/role/${roleId}`) }
