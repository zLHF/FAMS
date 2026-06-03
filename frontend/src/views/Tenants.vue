<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-input v-model="filters.name" placeholder="租户名称" clearable style="width:200px;" @keyup.enter="loadData" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:130px;">
          <el-option label="启用" value="active" /><el-option label="停用" value="disabled" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" class="btn-green" @click="openDialog()">新增租户</el-button>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <template v-else>
        <el-table :data="tableData" stripe>
          <el-table-column prop="name" label="租户名称" min-width="140" />
          <el-table-column prop="code" label="租户编码" width="180" />
          <el-table-column prop="member_count" label="成员数" width="90" align="center" />
          <el-table-column label="状态" width="80">
            <template #default="{row}">
              <el-tag :type="row.status==='active'?'success':'danger'" size="small">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
            <template #default="{row}">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="260">
            <template #default="{row}">
              <el-button link type="primary" @click="openDialog(row)">修改</el-button>
              <el-button link :type="row.status==='active'?'warning':'success'" @click="toggleStatus(row)">
                {{ row.status === 'active' ? '停用' : '启用' }}
              </el-button>
              <el-button link type="info" @click="viewMembers(row)">成员</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display:flex;justify-content:flex-end;margin-top:16px;">
          <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.per_page"
            v-model:current-page="filters.page" @current-change="loadData" />
        </div>
      </template>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '修改租户' : '新增租户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="租户名称" required>
          <el-input v-model="form.name" placeholder="请输入租户名称" />
        </el-form-item>
        <el-form-item label="租户编码" required>
          <el-input v-model="form.code" :disabled="!!editing" placeholder="请输入租户编码（唯一标识）" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 成员列表对话框 -->
    <el-dialog v-model="membersVisible" :title="`成员列表 - ${membersTenantName}`" width="650px">
      <el-table :data="members" stripe v-loading="membersLoading">
        <el-table-column prop="username" label="账号" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="department" label="部门" />
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag :type="row.status==='active'?'success':'info'" size="small">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!membersLoading && members.length === 0" description="该租户暂无成员" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTenants, createTenant, updateTenant, deleteTenant, getTenantMembers } from '../api/tenants'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const filters = ref({ name: '', status: '', page: 1, per_page: 10 })
const tableData = ref([])
const total = ref(0)

const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', code: '', statusBool: true })

const membersVisible = ref(false)
const membersLoading = ref(false)
const members = ref([])
const membersTenantName = ref('')

async function loadData() {
  loading.value = true
  try {
    const r = await getTenants(filters.value)
    tableData.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

function openDialog(row = null) {
  editing.value = row
  form.value = row
    ? { ...row, statusBool: row.status === 'active' }
    : { name: '', code: '', statusBool: true }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.name || !form.value.code) {
    ElMessage.warning('租户名称和编码不能为空')
    return
  }
  const data = { name: form.value.name, code: form.value.code, status: form.value.statusBool ? 'active' : 'disabled' }
  if (editing.value) {
    await updateTenant(editing.value.id, data)
  } else {
    await createTenant(data)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function toggleStatus(row) {
  const s = row.status === 'active' ? 'disabled' : 'active'
  await updateTenant(row.id, { status: s })
  ElMessage.success(s === 'active' ? '已启用' : '已停用')
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除租户 "${row.name}"？仅无活跃成员的租户可删除。`, '删除确认', { type: 'warning' })
  await deleteTenant(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function viewMembers(row) {
  membersTenantName.value = row.name
  membersVisible.value = true
  membersLoading.value = true
  try {
    const r = await getTenantMembers(row.id)
    members.value = r.items
  } finally {
    membersLoading.value = false
  }
}

function formatTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 19)
}

onMounted(() => { loadData() })
</script>
