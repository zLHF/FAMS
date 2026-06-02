<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;align-items:flex-end;">
        <el-input v-model="filters.code" placeholder="资产编码" clearable style="width:160px;" @keyup.enter="loadData" />
        <el-input v-model="filters.name" placeholder="资产名称" clearable style="width:160px;" @keyup.enter="loadData" />
        <el-button @click="loadData">查询</el-button>
      </div>
    </el-card>
    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <template v-else>
        <el-table :data="tableData" stripe>
          <el-table-column prop="code" label="资产编码" /><el-table-column prop="name" label="资产名称" />
          <el-table-column label="当前状态" width="100"><template #default="{row}"><el-tag :type="statusType(row.status)" size="small">{{statusLabel[row.status]}}</el-tag></template></el-table-column>
          <el-table-column prop="owner_name" label="领用人" />
          <el-table-column prop="location" label="存放地点" />
          <el-table-column label="操作" width="100">
            <template #default="{row}">
              <el-button v-if="row.status==='idle'||row.status==='returned'" link type="primary" @click="openDialog(row)">派发</el-button>
              <span v-else style="color:#999;font-size:13px;">—</span>
            </template>
          </el-table-column>
        </el-table>
        <div style="display:flex;justify-content:flex-end;margin-top:16px;">
          <el-pagination background layout="total,prev,pager,next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
        </div>
      </template>
    </el-card>

    <el-dialog v-model="dialogVisible" title="资产派发" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="资产编码"><el-input :model-value="currentAsset?.code" disabled /></el-form-item>
        <el-form-item label="资产名称"><el-input :model-value="currentAsset?.name" disabled /></el-form-item>
        <el-form-item label="领用人" required>
          <el-select v-model="form.owner_id" placeholder="请选择领用人" style="width:100%;" filterable>
            <el-option v-for="u in users" :key="u.id" :label="`${u.name}（${u.department||'无部门'}）`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="派发日期"><el-date-picker v-model="form.distribute_date" type="date" value-format="YYYY-MM-DD" style="width:100%;" /></el-form-item>
        <el-form-item label="使用地点" required>
          <el-select v-model="form.location" style="width:100%;"><el-option v-for="l in locations" :key="l.name" :label="l.name" :value="l.name" /></el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="handleSave">确认派发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAssets, distributeAsset } from '../api/assets'
import { getUsers } from '../api/users'
import { getParamOptions } from '../api/assetParams'
import { ElMessage } from 'element-plus'

const statusLabel = {idle:'闲置',distributed:'已派发',borrowing:'借用中',returned:'已退库'}
const statusType = {idle:'success',distributed:'warning',borrowing:'',returned:'info'}
const loading = ref(false)
const filters = ref({code:'',name:'',status:'',page:1,per_page:10})
const tableData = ref([]); const total = ref(0)
const dialogVisible = ref(false); const currentAsset = ref(null)
const users = ref([]); const locations = ref([])
const form = ref({owner_id:'',distribute_date:'',location:'',notes:''})

async function loadData() {
  loading.value = true
  try {
    const r=await getAssets(filters.value); tableData.value=r.items; total.value=r.total
  } finally {
    loading.value = false
  }
}
async function loadUsers() { const r=await getUsers({per_page:100,status:'active'}); users.value=r.items }
async function loadOptions() { const r=await getParamOptions(); locations.value=r.location||[] }

function openDialog(row) {
  currentAsset.value = row
  const today = new Date().toISOString().slice(0,10)
  form.value = {owner_id:'',distribute_date:today,location:row.location||'',notes:''}
  dialogVisible.value = true
}

async function handleSave() {
  await distributeAsset(currentAsset.value.id, form.value)
  ElMessage.success('派发成功'); dialogVisible.value=false; loadData()
}

onMounted(() => { loadData(); loadUsers(); loadOptions() })
</script>
