import http from './index'
export function getAssets(params) { return http.get('/assets', { params }) }
export function getAsset(id) { return http.get(`/assets/${id}`) }
export function createAsset(data) { return http.post('/assets', data) }
export function updateAsset(id, data) { return http.put(`/assets/${id}`, data) }
export function distributeAsset(id, data) { return http.post(`/assets/${id}/distribute`, data) }
export function borrowAsset(id, data) { return http.post(`/assets/${id}/borrow`, data) }
export function returnAsset(id, data) { return http.post(`/assets/${id}/return`, data) }
export function revertAsset(id, data) { return http.post(`/assets/${id}/revert`, data) }
export function changeOwner(id, data) { return http.post(`/assets/${id}/owner-change`, data) }
export function getFlowRecords(id) { return http.get(`/assets/${id}/records`) }
