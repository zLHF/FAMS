import http from './index'
export function getStats() { return http.get('/dashboard/stats') }
export function getRecentAssets() { return http.get('/dashboard/recent-assets') }
export function getLogs(params) { return http.get('/operation-logs', { params }) }
