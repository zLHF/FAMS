<template>
  <div class="sso-callback">
    <div class="sso-callback__content">
      <template v-if="loading">
        <el-icon class="sso-callback__spinner" :size="40"><Loading /></el-icon>
        <p class="sso-callback__text">正在登录中...</p>
      </template>
      <template v-else-if="error">
        <el-icon class="sso-callback__error" :size="40"><CircleCloseFilled /></el-icon>
        <p class="sso-callback__text">登录失败</p>
        <p class="sso-callback__detail">{{ error }}</p>
        <el-button type="primary" @click="goLogin" class="sso-callback__btn">
          返回登录页
        </el-button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { ssoCallback } from '../api/sso'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    error.value = '缺少授权码'
    loading.value = false
    return
  }

  try {
    const res = await ssoCallback(code)
    authStore.persistSession(res)

    // 清理 URL 中的 code 参数
    window.history.replaceState({}, '', window.location.pathname)
    router.replace('/')
  } catch (err) {
    const msg = err.response?.data?.error || 'SSO 登录失败，请稍后重试'
    error.value = msg
  } finally {
    loading.value = false
  }
})

function goLogin() {
  router.replace('/login')
}
</script>

<style scoped>
.sso-callback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
}

.sso-callback__content {
  text-align: center;
  padding: 48px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.sso-callback__spinner {
  color: var(--el-color-primary);
  animation: rotate 1.5s linear infinite;
}

.sso-callback__error {
  color: var(--el-color-danger);
}

.sso-callback__text {
  margin-top: 16px;
  font-size: 16px;
  color: #303133;
}

.sso-callback__detail {
  margin-top: 8px;
  font-size: 14px;
  color: #909399;
}

.sso-callback__btn {
  margin-top: 20px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
