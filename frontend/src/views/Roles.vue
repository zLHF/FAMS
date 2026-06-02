<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;align-items:flex-end;">
        <el-input v-model="filters.name" placeholder="角色名称" clearable style="width:200px;" @keyup.enter="loadData" />
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" class="btn-green" @click="openDialog()">新增角色</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="tableData" stripe>
        <el-table-column prop="name" label="角色名称" /><el-table-column prop="code" label="角色编码" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="状态" width="80">
          <template #default="{row}"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{row.status==='active'?'启用':'停用'}}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{row}">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link type="success" @click="openPermDialog(row)">分配权限</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing?'修改角色':'新增角色'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="角色名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="角色编码" required><el-input v-model="form.code" :disabled="!!editing" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="permDialogVisible" title="分配权限" width="500px">
      <el-tree v-if="permTree.length" ref="treeRef" :data="permTree" :props="{label:'name',children:'children'}" show-checkbox node-key="id" :default-checked-keys="checkedKeys" />
      <template #footer>
        <el-button @click="permDialogVisible=false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="savePermissions">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRoles, createRole, updateRole, deleteRole, assignPermissions } from '../api/roles'
import { getPermissionTree, getRolePermissions } from '../api/permissions'
import { ElMessage, ElMessageBox } from 'element-plus'

const filters = ref({name:''})
const tableData = ref([]); const dialogVisible = ref(false); const editing = ref(null)
const form = ref({name:'',code:'',description:'',statusBool:true})
const permDialogVisible = ref(false); const permTree = ref([]); const checkedKeys = ref([]); const currentRole = ref(null); const treeRef = ref(null)

async function loadData() { const r = await getRoles(filters.value); tableData.value = r.items }

function openDialog(role=null) {
  editing.value = role
  form.value = role ? {...role,statusBool:role.status==='active'} : {name:'',code:'',description:'',statusBool:true}
  dialogVisible.value = true
}

async function handleSave() {
  const data = {...form.value,status:form.value.statusBool?'active':'disabled'}
  if (editing.value) { await updateRole(editing.value.id,data) } else { await createRole(data) }
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function handleDelete(role) {
  await ElMessageBox.confirm(`确认删除角色 "${role.name}"？`,'提示',{type:'warning'})
  await deleteRole(role.id); ElMessage.success('删除成功'); loadData()
}

async function openPermDialog(role) {
  currentRole.value = role
  const [treeRes, permRes] = await Promise.all([getPermissionTree(), getRolePermissions(role.id)])
  const items = treeRes.items; const map = {}; const roots = []
  items.forEach(i => { map[i.id] = {...i, children:[]} })
  items.forEach(i => { if(i.parent_id && map[i.parent_id]) map[i.parent_id].children.push(map[i.id]); else roots.push(map[i.id]) })
  permTree.value = roots
  const parentIds = new Set(items.filter(i=>i.parent_id).map(i=>i.parent_id))
  checkedKeys.value = permRes.permission_ids.filter(id => !parentIds.has(id))
  permDialogVisible.value = true
}

async function savePermissions() {
  const checked = treeRef.value.getCheckedKeys(false)
  const half = treeRef.value.getHalfCheckedKeys()
  await assignPermissions(currentRole.value.id, [...checked,...half])
  ElMessage.success('权限分配成功'); permDialogVisible.value = false
}

onMounted(loadData)
</script>
