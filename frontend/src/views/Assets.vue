<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-input v-model="filters.code" placeholder="资产编码" clearable style="width:150px;" @keyup.enter="loadData" />
        <el-input v-model="filters.name" placeholder="资产名称" clearable style="width:150px;" @keyup.enter="loadData" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;">
          <el-option label="闲置" value="idle" /><el-option label="已派发" value="distributed" />
          <el-option label="借用中" value="borrowing" /><el-option label="已退库" value="returned" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" class="btn-green" @click="openDialog()">新增资产</el-button>
      </div>
    </el-card>
    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
      <template v-else>
        <el-table :data="tableData" stripe>
          <el-table-column prop="code" label="资产编码" width="100" /><el-table-column prop="name" label="资产名称" />
          <el-table-column prop="category" label="分类" width="100" /><el-table-column prop="brand" label="品牌" width="80" />
          <el-table-column prop="location" label="存放地点" />
          <el-table-column label="状态" width="90">
            <template #default="{row}"><el-tag :type="statusType[row.status]" size="small">{{statusLabel[row.status]}}</el-tag></template>
          </el-table-column>
          <el-table-column prop="owner_name" label="责任人" width="80" />
          <el-table-column label="操作" width="140">
            <template #default="{row}">
              <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
              <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display:flex;justify-content:flex-end;margin-top:16px;">
          <el-pagination background layout="total,prev,pager,next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
        </div>
      </template>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="readonly?'资产详情':(editing?'修改资产':'新增资产')" width="700px">
      <el-form :model="form" label-width="80px" :disabled="readonly">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px;">
          <el-form-item label="资产编码" required><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="资产名称" required><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="资产分类"><el-select v-model="form.category" style="width:100%;"><el-option v-for="c in options.category||[]" :key="c.name" :label="c.name" :value="c.name" /></el-select></el-form-item>
          <el-form-item label="品牌"><el-select v-model="form.brand" clearable style="width:100%;"><el-option v-for="b in options.brand||[]" :key="b.name" :label="b.name" :value="b.name" /></el-select></el-form-item>
          <el-form-item label="型号"><el-input v-model="form.model" /></el-form-item>
          <el-form-item label="序列号"><el-input v-model="form.serial_number" /></el-form-item>
          <el-form-item label="计量单位"><el-select v-model="form.unit" style="width:100%;"><el-option v-for="u in options.unit||[]" :key="u.name" :label="u.name" :value="u.name" /></el-select></el-form-item>
          <el-form-item label="购置日期"><el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width:100%;" /></el-form-item>
          <el-form-item label="存放地点"><el-select v-model="form.location" style="width:100%;"><el-option v-for="l in options.location||[]" :key="l.name" :label="l.name" :value="l.name" /></el-select></el-form-item>
          <el-form-item label="当前状态"><el-select v-model="form.status" style="width:100%;"><el-option label="闲置" value="idle" /><el-option label="已派发" value="distributed" /><el-option label="借用中" value="borrowing" /><el-option label="已退库" value="returned" /></el-select></el-form-item>
        </div>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer v-if="!readonly">
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" class="btn-green" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAssets, getAsset, createAsset, updateAsset } from '../api/assets'
import { getParamOptions } from '../api/assetParams'
import { ElMessage } from 'element-plus'

const statusLabel = {idle:'闲置',distributed:'已派发',borrowing:'借用中',returned:'已退库'}
const statusType = {idle:'success',distributed:'warning',borrowing:'danger',returned:'info'}
const loading = ref(false)
const filters = ref({code:'',name:'',status:'',page:1,per_page:10})
const tableData = ref([]); const total = ref(0); const dialogVisible = ref(false)
const editing = ref(null); const readonly = ref(false); const options = ref({})
const form = ref({code:'',name:'',category:'',brand:'',model:'',serial_number:'',unit:'',purchase_date:'',location:'',status:'idle',notes:''})

async function loadData() {
  loading.value = true
  try {
    const r=await getAssets(filters.value); tableData.value=r.items; total.value=r.total
  } finally {
    loading.value = false
  }
}
async function loadOptions() { options.value = await getParamOptions() }

function openDialog(row=null) {
  readonly.value = false; editing.value = row
  form.value = row ? {...row} : {code:'',name:'',category:'',brand:'',model:'',serial_number:'',unit:'',purchase_date:'',location:'',status:'idle',notes:''}
  dialogVisible.value = true
}

async function viewDetail(row) {
  const detail = await getAsset(row.id); form.value = detail; editing.value = detail; readonly.value = true; dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.code || !form.value.name) { ElMessage.warning('资产编码和名称为必填'); return }
  try {
    if (editing.value?.id) { await updateAsset(editing.value.id, form.value) } else { await createAsset(form.value) }
    ElMessage.success('保存成功'); dialogVisible.value=false; loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '保存失败')
  }
}

onMounted(() => { loadData(); loadOptions() })
</script>
