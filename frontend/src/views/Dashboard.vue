<template>
  <div>
    <div class="metrics">
      <div v-for="m in metricList" :key="m.key" class="metric">
        <span>{{ m.label }}</span>
        <strong>{{ stats[m.key] || 0 }}</strong>
      </div>
    </div>

    <div class="content-grid">
      <div class="panel">
        <div class="panel-head"><h2>最近资产</h2></div>
        <el-table :data="recentAssets" stripe size="small">
          <el-table-column prop="code" label="编码" width="90" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="owner_name" label="责任人" width="80" />
        </el-table>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>快捷入口</h2></div>
        <div class="quick-actions">
          <router-link v-for="q in quickLinks" :key="q.path" :to="q.path">
            <el-button style="width:100%;">{{ q.label }}</el-button>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats, getRecentAssets } from '../api/dashboard'

const statusLabel = { idle: '闲置', distributed: '已派发', borrowing: '借用中', returned: '已退库' }
const statusType = { idle: 'success', distributed: 'warning', borrowing: '', returned: 'info' }

const stats = ref({})
const recentAssets = ref([])

const metricList = [
  { key: 'total', label: '资产总数' },
  { key: 'idle', label: '闲置资产' },
  { key: 'distributed', label: '已派发' },
  { key: 'borrowing', label: '借用中' },
]

const quickLinks = [
  { path: '/assets', label: '新增资产' },
  { path: '/asset-distribute', label: '资产派发' },
  { path: '/asset-borrow', label: '借用登记' },
  { path: '/asset-return', label: '归还登记' },
]

async function load() {
  const [s, r] = await Promise.all([getStats(), getRecentAssets()])
  stats.value = s
  recentAssets.value = r.items
}

onMounted(load)
</script>

<style scoped>
.metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:16px; }
.metric { background:#fff; border:1px solid #dde5ed; border-radius:8px; padding:18px; }
.metric span { display:block; color:#66788a; font-size:14px; }
.metric strong { display:block; font-size:30px; margin:8px 0; color:#102a43; }
.content-grid { display:grid; grid-template-columns:1.1fr .9fr; gap:16px; }
.panel { background:#fff; border:1px solid #dde5ed; border-radius:8px; padding:18px; }
.panel-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.panel-head h2 { font-size:17px; margin:0; }
.quick-actions { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
@media(max-width:900px) { .metrics, .content-grid { grid-template-columns:1fr; } }
</style>
