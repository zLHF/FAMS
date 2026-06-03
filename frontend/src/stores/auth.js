import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, logout as logoutApi, getMe, switchTenant as switchTenantApi } from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('fams_user') || 'null'))
  const token = ref(localStorage.getItem('fams_token') || '')
  const currentTenant = ref(JSON.parse(localStorage.getItem('fams_tenant') || 'null'))
  const tenants = ref(JSON.parse(localStorage.getItem('fams_tenants') || '[]'))

  function persistSession(res) {
    token.value = res.token
    user.value = res.user
    currentTenant.value = res.tenant || res.user?.tenant || null
    tenants.value = res.tenants || res.user?.tenants || []
    localStorage.setItem('fams_token', token.value)
    localStorage.setItem('fams_user', JSON.stringify(user.value))
    localStorage.setItem('fams_tenant', JSON.stringify(currentTenant.value))
    localStorage.setItem('fams_tenants', JSON.stringify(tenants.value))
  }

  function clearSession() {
    token.value = ''
    user.value = null
    currentTenant.value = null
    tenants.value = []
    localStorage.removeItem('fams_token')
    localStorage.removeItem('fams_user')
    localStorage.removeItem('fams_tenant')
    localStorage.removeItem('fams_tenants')
  }

  async function login(username, password, tenantId) {
    const res = await loginApi({ username, password, tenant_id: tenantId })
    persistSession(res)
    return res
  }

  async function switchTenant(tenantId) {
    const res = await switchTenantApi(tenantId)
    persistSession(res)
    return res
  }

  async function logout() {
    try { await logoutApi() } catch {}
    clearSession()
    router.push('/login')
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res
      currentTenant.value = res.tenant || currentTenant.value
      tenants.value = res.tenants || tenants.value
      localStorage.setItem('fams_user', JSON.stringify(user.value))
      localStorage.setItem('fams_tenant', JSON.stringify(currentTenant.value))
      localStorage.setItem('fams_tenants', JSON.stringify(tenants.value))
    } catch {
      clearSession()
    }
  }

  return { user, token, currentTenant, tenants, login, logout, fetchUser, switchTenant, clearSession }
})
