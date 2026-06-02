<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-input v-model="filters.name" placeholder="用户姓名/账号" clearable style="width:200px;" @keyup.enter="loadData" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:130px;">
          <el-option label="启用" value="active" /><el-option label="停用" value="disabled" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" class="btn-green" @click="openDialog()">新增用户</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="tableData" stripe>
        <el-table-column prop="username" label="账号" /><el-table-column prop="name" label="姓名" />
        <el-table-column prop="department" label="部门" /><el-table-column prop="role_name" label="角色" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column label="状态" width="80">
          <template #default="{row}"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{row.status==='active'?'启用':'停用'}}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{row}">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link :type="row.status==='active'?'warning':'success'" @click="toggleStatus(row)">{{row.status==='active'?'停用':'启用'}}</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing?'修改用户':'新增用户'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户账号" required><el-input v-model="form.username" :disabled="!!editing" /></el-form-item>
        <el-form-item label="用户姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="所属部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role_id" placeholder="请选择角色" style="width:100%;"><el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="!editing" label="密码"><el-input v-model="form.password" type="password" placeholder="默认 123456" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '../api/users'
import { getRoles } from '../api/roles'
import { ElMessage, ElMessageBox } from 'element-plus'

const filters = ref({ name: '', status: '', page: 1, per_page: 10 })
const tableData = ref([]); const total = ref(0)
const dialogVisible = ref(false); const editing = ref(null); const roleOptions = ref([])
const form = ref({ username:'',name:'',phone:'',department:'',role_id:'',password:'',statusBool:true })

async function loadData() { const r = await getUsers(filters.value); tableData.value = r.items; total.value = r.total }
async function loadRoles() { const r = await getRoles({per_page:100}); roleOptions.value = r.items }

function openDialog(row=null) {
  editing.value = row
  form.value = row ? {...row, statusBool:row.status==='active', password:''} : {username:'',name:'',phone:'',department:'',role_id:'',password:'',statusBool:true}
  dialogVisible.value = true
}

async function handleSave() {
  const data = {...form.value, status: form.value.statusBool?'active':'disabled'}; delete data.statusBool
  if (editing.value) { await updateUser(editing.value.id, data) } else { await createUser(data) }
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function toggleStatus(row) {
  const s = row.status==='active'?'disabled':'active'
  await updateUser(row.id, {status:s}); ElMessage.success(s==='active'?'已启用':'已停用'); loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除用户 "${row.name}"？`,'删除确认',{type:'warning'})
  await deleteUser(row.id); ElMessage.success('删除成功'); loadData()
}

onMounted(() => { loadData(); loadRoles() })
</script>
