<template>
  <div class="topbar">
    <div>
      <h1>{{ title }}</h1>
      <p>{{ subtitle }}</p>
    </div>
    <div class="right-tools">
      <el-select
        v-if="auth.tenants.length"
        :model-value="auth.currentTenant?.id"
        size="small"
        class="tenant-select"
        @change="handleTenantChange"
      >
        <el-option v-for="tenant in auth.tenants" :key="tenant.id" :label="tenant.name" :value="tenant.id" />
      </el-select>
      <div class="user-chip">
        {{ auth.user?.name || '未登录' }}
        <el-button link type="danger" @click="auth.logout()" style="margin-left:8px;" aria-label="退出登录">退出</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

defineProps({ title: String, subtitle: String })
const auth = useAuthStore()
const router = useRouter()

async function handleTenantChange(tenantId) {
  if (tenantId === auth.currentTenant?.id) return
  await auth.switchTenant(tenantId)
  ElMessage.success('已切换租户')
  router.push('/')
}
</script>

<style scoped>
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; gap:16px; }
.topbar h1 { font-size:24px; margin:0 0 6px; }
.topbar p { margin:0; color:#66788a; }
.right-tools { display:flex; align-items:center; gap:12px; }
.tenant-select { width:160px; }
.user-chip { background:#fff; border:1px solid #d9e2ec; border-radius:999px; padding:8px 14px; color:#334e68; font-size:14px; white-space:nowrap; }
</style>
