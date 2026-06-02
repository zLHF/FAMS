<template>
  <div>
    <div class="permission-layout">
      <el-card shadow="never">
        <template #header>选择角色</template>
        <div v-for="r in roles" :key="r.id">
          <div class="role-option" :class="{active:selectedRole?.id===r.id}" @click="selectRole(r)">{{ r.name }}</div>
        </div>
      </el-card>
      <el-card shadow="never">
        <template #header>权限配置 — {{ selectedRole?.name || '请选择角色' }}</template>
        <el-tree v-if="selectedRole && permTree.length" ref="treeRef" :data="permTree" :props="{label:'name',children:'children'}" show-checkbox node-key="id" :default-checked-keys="checkedKeys" />
        <p v-else style="color:#999;">请先在左侧选择一个角色</p>
        <div v-if="selectedRole" style="margin-top:16px;text-align:right;">
          <el-button type="primary" class="btn-green" @click="savePermissions">保存权限</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRoles, assignPermissions } from '../api/roles'
import { getPermissionTree, getRolePermissions } from '../api/permissions'
import { ElMessage } from 'element-plus'

const roles = ref([]); const selectedRole = ref(null)
const permTree = ref([]); const checkedKeys = ref([]); const treeRef = ref(null)

async function loadRoles() { const r = await getRoles({per_page:100}); roles.value = r.items }

async function selectRole(role) {
  selectedRole.value = role
  const [treeRes, permRes] = await Promise.all([getPermissionTree(), getRolePermissions(role.id)])
  const items = treeRes.items; const map = {}; const roots = []
  items.forEach(i => { map[i.id] = {...i, children:[]} })
  items.forEach(i => { if(i.parent_id && map[i.parent_id]) map[i.parent_id].children.push(map[i.id]); else roots.push(map[i.id]) })
  permTree.value = roots
  const parentIds = new Set(items.filter(i=>i.parent_id).map(i=>i.parent_id))
  checkedKeys.value = permRes.permission_ids.filter(id => !parentIds.has(id))
}

async function savePermissions() {
  const checked = treeRef.value.getCheckedKeys(false)
  const half = treeRef.value.getHalfCheckedKeys()
  await assignPermissions(selectedRole.value.id, [...checked,...half])
  ElMessage.success('保存成功')
}

onMounted(loadRoles)
</script>

<style scoped>
.permission-layout { display:grid; grid-template-columns:260px 1fr; gap:16px; }
.role-option { width:100%; text-align:left; border:1px solid #d9e2ec; background:#fff; border-radius:6px; padding:11px 12px; margin-bottom:10px; cursor:pointer; transition:all .15s; }
.role-option:hover { border-color:#16805f; }
.role-option.active { background:#e3f8ef; border-color:#21a67a; color:#13795b; }
</style>
