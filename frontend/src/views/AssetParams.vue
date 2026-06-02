<template>
  <div>
    <el-card shadow="never" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-select v-model="filters.type" placeholder="参数类型" clearable style="width:160px;">
          <el-option label="资产分类" value="category" /><el-option label="品牌" value="brand" />
          <el-option label="计量单位" value="unit" /><el-option label="存放地点" value="location" />
        </el-select>
        <el-input v-model="filters.name" placeholder="参数名称" clearable style="width:200px;" @keyup.enter="loadData" />
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" class="btn-green" @click="openDialog()">新增参数</el-button>
      </div>
    </el-card>
    <el-card shadow="never">
      <el-table :data="tableData" stripe>
        <el-table-column prop="type" label="参数类型"><template #default="{row}">{{typeMap[row.type]||row.type}}</template></el-table-column>
        <el-table-column prop="name" label="参数名称" /><el-table-column prop="code" label="编码" />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{row.status==='active'?'启用':'停用'}}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{row}">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <el-pagination background layout="total,prev,pager,next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing?'修改参数':'新增参数'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="参数类型" required>
          <el-select v-model="form.type" style="width:100%;"><el-option label="资产分类" value="category" /><el-option label="品牌" value="brand" /><el-option label="计量单位" value="unit" /><el-option label="存放地点" value="location" /></el-select>
        </el-form-item>
        <el-form-item label="参数名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
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
import { getAssetParams, createAssetParam, updateAssetParam, deleteAssetParam } from '../api/assetParams'
import { ElMessage, ElMessageBox } from 'element-plus'

const typeMap = {category:'资产分类',brand:'品牌',unit:'计量单位',location:'存放地点'}
const filters = ref({type:'',name:'',page:1,per_page:20})
const tableData = ref([]); const total = ref(0); const dialogVisible = ref(false); const editing = ref(null)
const form = ref({type:'category',name:'',code:'',sort_order:0,statusBool:true})

async function loadData() { const r = await getAssetParams(filters.value); tableData.value=r.items; total.value=r.total }

function openDialog(row=null) {
  editing.value = row
  form.value = row ? {...row,statusBool:row.status==='active'} : {type:'category',name:'',code:'',sort_order:0,statusBool:true}
  dialogVisible.value = true
}

async function handleSave() {
  const data = {...form.value,status:form.value.statusBool?'active':'disabled'}; delete data.statusBool
  if (editing.value) { await updateAssetParam(editing.value.id,data) } else { await createAssetParam(data) }
  ElMessage.success('保存成功'); dialogVisible.value=false; loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除参数 "${row.name}"？`,'提示',{type:'warning'})
  await deleteAssetParam(row.id); ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>
