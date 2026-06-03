import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/sso-callback',
    name: 'SSOCallback',
    component: () => import('../views/SSOCallback.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'users', name: 'Users', component: () => import('../views/Users.vue') },
      { path: 'tenants', name: 'Tenants', component: () => import('../views/Tenants.vue') },
      { path: 'roles', name: 'Roles', component: () => import('../views/Roles.vue') },
      { path: 'permissions', name: 'Permissions', component: () => import('../views/Permissions.vue') },
      { path: 'asset-params', name: 'AssetParams', component: () => import('../views/AssetParams.vue') },
      { path: 'assets', name: 'Assets', component: () => import('../views/Assets.vue') },
      { path: 'asset-distribute', name: 'AssetDistribute', component: () => import('../views/AssetDistribute.vue') },
      { path: 'asset-borrow', name: 'AssetBorrow', component: () => import('../views/AssetBorrow.vue') },
      { path: 'asset-return', name: 'AssetReturn', component: () => import('../views/AssetReturn.vue') },
      { path: 'asset-revert', name: 'AssetRevert', component: () => import('../views/AssetRevert.vue') },
      { path: 'asset-owner-change', name: 'AssetOwnerChange', component: () => import('../views/AssetOwnerChange.vue') },
      { path: 'logs', name: 'Logs', component: () => import('../views/OperationLogs.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('fams_token')

  // SSO 回调检测：URL 中有 code 参数
  const urlParams = new URLSearchParams(window.location.search)
  const ssoCode = urlParams.get('code')

  if (ssoCode) {
    if (token) {
      // 已有 token，清理 code 参数后继续
      window.history.replaceState({}, '', window.location.pathname)
    } else if (to.name !== 'SSOCallback') {
      // 无 token，跳转到 SSO 回调处理页
      return { path: '/sso-callback', query: { code: ssoCode } }
    }
  }

  if (!to.meta?.public && !token) return { path: '/login' }
})

export default router
