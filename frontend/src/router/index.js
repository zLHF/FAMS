import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'users', name: 'Users', component: () => import('../views/Users.vue') },
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
  if (!to.meta?.public && !token) return { path: '/login' }
})

export default router
