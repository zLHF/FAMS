import http from './index'
export function login(data) { return http.post('/auth/login', data) }
export function logout() { return http.post('/auth/logout') }
export function getMe() { return http.get('/auth/me') }
