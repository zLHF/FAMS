<template>
  <div class="login-page">
    <div class="login-shell">
      <div class="login-visual">
        <div class="brand-row">
          <div style="width:42px;height:42px;border-radius:8px;background:#21a67a;display:grid;place-items:center;color:#fff;font-weight:800;font-size:18px;">资</div>
          <div><strong style="color:#fff">固定资产管理系统</strong><br><span>Fixed Asset Management</span></div>
        </div>
        <h1 style="color:#fff;font-size:32px;line-height:1.3;margin:40px 0;">企业固定资产<br>数字化管理平台</h1>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:auto;">
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">{{ publicStats.total || '—' }}</b><br><span style="color:#bcccdc;font-size:12px;">资产总数</span>
          </div>
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">{{ publicStats.idle || '—' }}</b><br><span style="color:#bcccdc;font-size:12px;">闲置资产</span>
          </div>
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">{{ publicStats.borrowing || '—' }}</b><br><span style="color:#bcccdc;font-size:12px;">借用中</span>
          </div>
        </div>
      </div>
      <div class="login-card">
        <h2>欢迎登录</h2>
        <p style="color:#7b8794">请输入账号和密码，系统会自动进入默认租户</p>
        <el-form :model="form" @submit.prevent="handleLogin" style="margin-top:24px;">
          <el-form-item>
            <el-input v-model="form.username" placeholder="请输入账号" size="large" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password />
          </el-form-item>
          <el-button type="primary" size="large" style="width:100%;background:#16805f;border-color:#16805f;" :loading="loading" native-type="submit">
            登录系统
          </el-button>
        </el-form>
        <p v-if="isDev" style="color:#7b8794;font-size:13px;margin-top:16px;">开发模式 — 默认账号见 README</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getStats } from '../api/dashboard'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const isDev = import.meta.env.DEV
const form = ref({ username: '', password: '' })
const publicStats = ref({})

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    return ElMessage.warning('请输入账号和密码')
  }
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    const tenantName = auth.currentTenant?.name ? `（${auth.currentTenant.name}）` : ''
    ElMessage.success(`登录成功${tenantName}`)
    router.push('/')
  } catch {} finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const s = await getStats()
    publicStats.value = s
  } catch {
    // not logged in, show dashes
  }
})
</script>

<style scoped>
.login-page { min-height:100vh; display:grid; place-items:center; background:linear-gradient(135deg,#102a43,#243b53 48%,#1f513f); padding:28px; }
.login-shell { width:min(980px,100%); display:grid; grid-template-columns:1.15fr .85fr; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 28px 80px rgba(0,0,0,.25); }
.login-visual { background:#17212f; color:#fff; padding:42px; display:flex; flex-direction:column; justify-content:space-between; min-height:520px; }
.login-card { padding:46px 38px; display:grid; align-content:center; gap:4px; }
.brand-row { display:flex; gap:12px; align-items:center; }
.brand-row span { color:#bcccdc; font-size:13px; }
@media(max-width:900px) { .login-shell { grid-template-columns:1fr; } .login-visual { display:none; } }
</style>
