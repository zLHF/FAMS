const modal = document.getElementById('modal'); const form = document.getElementById('modalForm'); const title = document.getElementById('modalTitle'); const toast = document.getElementById('toast');
const schemas = {
  user:['用户账号','用户姓名','所属部门','手机号','角色','状态'],
  role:['角色名称','角色编码','角色描述','状态'],
  param:['参数类型','参数名称','参数编码','排序','状态'],
  asset:['资产编码','资产名称','资产分类','品牌','型号','序列号','计量单位','购置日期','存放地点','当前状态','备注'],
  distribute:['资产编码','领用人','领用部门','派发日期','存放地点','备注'],
  borrow:['资产编码','借用人','借用部门','借用日期','预计归还日期','借用原因'],
  return:['资产编码','归还日期','归还地点','资产状况','备注'],
  revert:['资产编码','原领用人','退库日期','退库地点','资产状况','备注'],
  owner:['资产编码','原领用人','新领用人','变更日期','使用地点','变更原因']
};
const titles = {user:'用户信息',role:'角色信息',param:'参数信息',asset:'固定资产信息',distribute:'固定资产派发',borrow:'固定资产借用',return:'借用归还',revert:'领用退库',owner:'变更领用人'};
function showToast(text){ if(!toast) return; toast.textContent=text; toast.classList.add('show'); setTimeout(()=>toast.classList.remove('show'),1800); }
function openModal(type){ if(!modal || !form) return; title.textContent=titles[type]||'操作'; form.innerHTML=''; (schemas[type]||[]).forEach((name,idx)=>{ const label=document.createElement('label'); if(name==='备注'||name.includes('原因')||name.includes('描述')) label.className='full'; label.textContent=name; let input; if(['状态','当前状态','资产状况','角色','资产分类','参数类型'].includes(name)){ input=document.createElement('select'); ['请选择','启用','停用','闲置','已派发','借用中','已退库','完好','损坏','需维修','系统管理员','资产管理员','普通用户','电脑设备','办公家具','网络设备'].forEach(v=>{ const o=document.createElement('option'); o.textContent=v; input.appendChild(o); }); } else if(name==='备注'||name.includes('原因')||name.includes('描述')){ input=document.createElement('textarea'); input.placeholder='请输入'+name; } else { input=document.createElement('input'); input.placeholder='请输入'+name; if(name.includes('日期')) input.type='date'; } label.appendChild(input); form.appendChild(label); }); modal.classList.add('show'); modal.setAttribute('aria-hidden','false'); }
document.addEventListener('click', e=>{ const m=e.target.closest('[data-modal]'); const d=e.target.closest('[data-demo]'); if(m){ openModal(m.dataset.modal); } if(d){ showToast(d.dataset.demo+'操作已触发，静态页面仅演示交互'); } if(e.target.closest('[data-close]')){ modal?.classList.remove('show'); modal?.setAttribute('aria-hidden','true'); } if(e.target.closest('[data-save]')){ modal?.classList.remove('show'); showToast('保存成功，后端接入后提交真实数据'); } });
