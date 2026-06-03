import http from './index'

/** SSO 登录回调 — 用平台生成的 code 换取本地登录凭证 */
export function ssoCallback(code) {
  return http.post('/sso/callback', { code })  // http baseURL='/api'，实际请求 /api/sso/callback
}
