<template>
  <div>
    <el-card shadow="never" v-loading="loading">
      <div style="display:flex;gap:12px;margin-bottom:16px;">
        <el-select v-model="filters.action" placeholder="操作类型" clearable style="width:150px;">
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="新增" value="create" />
          <el-option label="修改" value="update" />
          <el-option label="删除" value="delete" />
          <el-option label="派发" value="distribute" />
          <el-option label="借用" value="borrow" />
          <el-option label="归还" value="return" />
          <el-option label="退库" value="revert" />
          <el-option label="变更领用人" value="owner_change" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
      </div>
      <el-empty v-if="!loading && tableData.length === 0" description="暂无操作日志" />
      <template v-else>
        <el-table :data="tableData" stripe>
          <el-table-column prop="user_name" label="操作人" width="100" />
          <el-table-column prop="action" label="操作类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ actionLabels[row.action] || row.action }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="target_type" label="操作对象" width="100" />
          <el-table-column prop="detail" label="操作详情" show-overflow-tooltip />
          <el-table-column prop="created_at" label="操作时间" width="180" />
        </el-table>
        <div style="display:flex;justify-content:flex-end;margin-top:16px;">
          <el-pagination background layout="total,prev,pager,next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs } from '../api/dashboard'
const actionLabels = { login:'登录', logout:'登出', create:'新增', update:'修改', delete:'删除', distribute:'派发', borrow:'借用', return:'归还', revert:'退库', owner_change:'变更领用人' }
const loading = ref(false)
const filters = ref({ action: '', page: 1, per_page: 20 })
const tableData = ref([])
const total = ref(0)

async function loadData() {
  loading.value = true
  try {
    const r = await getLogs(filters.value)
    tableData.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
