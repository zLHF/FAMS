import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('fams_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.error || '请求失败'
    if (err.response?.status === 401) {
      localStorage.removeItem('fams_token')
      localStorage.removeItem('fams_user')
      localStorage.removeItem('fams_tenant')
      localStorage.removeItem('fams_tenants')
      router.push('/login')
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default http
