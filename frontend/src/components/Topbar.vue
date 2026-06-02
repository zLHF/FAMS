<template>
  <div class="topbar">
    <div>
      <h1>{{ title }}</h1>
      <p>{{ subtitle }}</p>
    </div>
    <div class="user-chip">
      {{ auth.user?.name || '未登录' }}
      <el-button link type="danger" @click="auth.logout()" style="margin-left:8px;" aria-label="退出登录">退出</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

defineProps({ title: String, subtitle: String })
const auth = useAuthStore()
</script>

<style scoped>
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; }
.topbar h1 { font-size:24px; margin:0 0 6px; }
.topbar p { margin:0; color:#66788a; }
.user-chip { background:#fff; border:1px solid #d9e2ec; border-radius:999px; padding:8px 14px; color:#334e68; font-size:14px; }
</style>
