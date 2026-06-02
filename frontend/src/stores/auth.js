import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, logout as logoutApi, getMe } from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('fams_user') || 'null'))
  const token = ref(localStorage.getItem('fams_token') || '')

  async function login(username, password) {
    const res = await loginApi({ username, password })
    token.value = res.token
    user.value = res.user
    localStorage.setItem('fams_token', res.token)
    localStorage.setItem('fams_user', JSON.stringify(res.user))
    return res
  }

  async function logout() {
    try { await logoutApi() } catch {}
    token.value = ''
    user.value = null
    localStorage.removeItem('fams_token')
    localStorage.removeItem('fams_user')
    router.push('/login')
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res
      localStorage.setItem('fams_user', JSON.stringify(res))
    } catch {
      token.value = ''
      user.value = null
      localStorage.removeItem('fams_token')
      localStorage.removeItem('fams_user')
    }
  }

  return { user, token, login, logout, fetchUser }
})
