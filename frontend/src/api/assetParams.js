import http from './index'
export function getAssetParams(params) { return http.get('/asset-params', { params }) }
export function createAssetParam(data) { return http.post('/asset-params', data) }
export function updateAssetParam(id, data) { return http.put(`/asset-params/${id}`, data) }
export function deleteAssetParam(id) { return http.delete(`/asset-params/${id}`) }
export function getParamOptions() { return http.get('/asset-params/options') }
