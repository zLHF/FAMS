<template>
  <Sidebar />
  <div class="main">
    <Topbar :title="title" :subtitle="subtitle" />
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

const route = useRoute()
const auth = useAuthStore()

const titleMap = {
  '/': '工作台', '/users': '用户管理', '/roles': '角色管理', '/permissions': '权限管理',
  '/asset-params': '资产参数设置', '/assets': '固定资产台账', '/asset-distribute': '资产派发',
  '/asset-borrow': '资产借用', '/asset-return': '借用归还', '/asset-revert': '领用退库',
  '/asset-owner-change': '变更领用人',
}
const title = computed(() => titleMap[route.path] || '固定资产管理系统')
const subtitle = computed(() => `欢迎，${auth.user?.name || ''}`)
</script>

<style scoped>
.main { margin-left:248px; min-height:100vh; padding:24px; background:#f4f6f8; }
@media(max-width:900px) { .main { margin-left:0; } }
</style>
