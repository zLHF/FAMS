<template>
  <Sidebar v-if="sidebarVisible" @navigate="sidebarVisible = false" />
  <div class="main" :class="{ 'sidebar-hidden': !sidebarVisible }">
    <div class="mobile-header">
      <button class="hamburger" @click="sidebarVisible = !sidebarVisible" aria-label="打开菜单">☰</button>
      <span class="mobile-title">{{ title }}</span>
    </div>
    <Topbar :title="title" :subtitle="subtitle" class="desktop-only" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

const route = useRoute()
const auth = useAuthStore()
const sidebarVisible = ref(window.innerWidth > 900)

const titleMap = {
  '/': '工作台', '/users': '用户管理', '/tenants': '租户管理', '/roles': '角色管理', '/permissions': '权限管理',
  '/asset-params': '资产参数设置', '/assets': '固定资产台账', '/asset-distribute': '资产派发',
  '/asset-borrow': '资产借用', '/asset-return': '借用归还', '/asset-revert': '领用退库',
  '/asset-owner-change': '变更领用人', '/logs': '操作日志',
}
const title = computed(() => titleMap[route.path] || '固定资产管理系统')
const subtitle = computed(() => `欢迎，${auth.user?.name || ''}`)
</script>

<style scoped>
.main { margin-left:248px; min-height:100vh; padding:24px; background:#f4f6f8; }
.mobile-header { display:none; }
.hamburger { display:none; }
.desktop-only {}
@media(max-width:900px) {
  .main { margin-left:0; }
  .main.sidebar-hidden { margin-left:0; }
  .mobile-header { display:flex; align-items:center; gap:12px; padding:12px 0; margin-bottom:16px; }
  .hamburger { display:block; width:40px; height:40px; border:1px solid #d9e2ec; border-radius:6px; background:#fff; font-size:20px; cursor:pointer; }
  .mobile-title { font-size:18px; font-weight:600; }
  .desktop-only { display:none; }
}
</style>
