<template>
  <div class="sidebar">
    <div class="brand">
      <div class="brand-mark">资</div>
      <div><strong>固定资产管理</strong><span>Fixed Asset Management</span></div>
    </div>
    <nav class="nav" role="navigation" aria-label="主导航">
      <router-link to="/" :class="{ active: isActive('/') }">
        <span></span>工作台
      </router-link>
      <div class="nav-group" v-if="isAdmin">
        <div class="nav-group-title">人员管理</div>
        <router-link v-for="item in personnelMenus" :key="item.path" :to="item.path" :class="{ active: isActive(item.path) }">
          <span></span>{{ item.label }}
        </router-link>
      </div>
      <div class="nav-group">
        <div class="nav-group-title">资产管理</div>
        <router-link to="/asset-params" :class="{ active: isActive('/asset-params') }">
          <span></span>资产参数设置
        </router-link>
        <router-link to="/assets" :class="{ active: isActive('/assets') }">
          <span></span>固定资产台账
        </router-link>
      </div>
      <div class="nav-group">
        <div class="nav-group-title">资产流转</div>
        <router-link v-for="item in flowMenus" :key="item.path" :to="item.path" :class="{ active: isActive(item.path) }">
          <span></span>{{ item.label }}
        </router-link>
      </div>
      <div class="nav-group">
        <div class="nav-group-title">系统管理</div>
        <router-link to="/logs" :class="{ active: isActive('/logs') }">
          <span></span>操作日志
        </router-link>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const isAdmin = computed(() => auth.user?.role === 'admin')

const personnelMenus = [
  { path: '/users', label: '用户管理' },
  { path: '/roles', label: '角色管理' },
  { path: '/permissions', label: '权限管理' },
]

const flowMenus = [
  { path: '/asset-distribute', label: '资产派发' },
  { path: '/asset-borrow', label: '资产借用' },
  { path: '/asset-return', label: '借用归还' },
  { path: '/asset-revert', label: '领用退库' },
  { path: '/asset-owner-change', label: '变更领用人' },
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.sidebar { position:fixed; inset:0 auto 0 0; width:248px; background:#17212f; color:#d9e2ec; padding:20px 16px; overflow:auto; }
.brand { display:flex; gap:12px; align-items:center; padding:4px 4px 22px; }
.brand-mark { width:42px; height:42px; border-radius:8px; background:#21a67a; color:#fff; display:grid; place-items:center; font-weight:800; font-size:18px; }
.brand strong { display:block; font-size:16px; color:#fff; }
.brand span { display:block; color:#9fb3c8; font-size:12px; margin-top:3px; }
.nav { display:grid; gap:4px; }
.nav a { display:flex; gap:10px; align-items:center; padding:10px 12px; border-radius:8px; color:#bcccdc; text-decoration:none; font-size:14px; transition:all .15s; }
.nav a span { width:7px; height:7px; border-radius:50%; background:#7b8794; flex-shrink:0; }
.nav a:hover, .nav a.active { background:#243447; color:#fff; }
.nav a.active span { background:#f5a623; }
.nav-group { display:grid; gap:2px; }
.nav-group-title { padding:14px 12px 6px; font-size:11px; text-transform:uppercase; letter-spacing:1px; color:#627089; font-weight:600; }
</style>
