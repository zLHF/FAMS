# 01 — 项目脚手架 + 数据库初始化

> **依赖:** 无
> **目标:** 搭建前后端项目骨架，数据库建表完成，能跑通 hello world。

---

## Task 1: 创建后端项目结构

**Files:**
- Create: `backend/run.py`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/extensions.py`

**Step 1: 创建目录结构**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统
mkdir -p backend/app/models backend/app/api backend/app/utils backend/tests backend/migrations
touch backend/app/__init__.py backend/app/models/__init__.py backend/app/api/__init__.py backend/app/utils/__init__.py
```

**Step 2: 创建 requirements.txt**

```
flask==3.1.1
flask-sqlalchemy==3.1.1
flask-migrate==4.1.0
flask-cors==5.0.1
flask-bcrypt==1.0.1
pyjwt==2.9.0
pytest==8.3.5
```

**Step 3: 创建 config.py**

```python
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fams-dev-secret-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "fams.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get("JWT_SECRET", "fams-jwt-secret-change-in-prod")
    JWT_EXPIRATION_HOURS = 24
```

**Step 4: 创建 extensions.py**

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
```

**Step 5: 创建 app/__init__.py (app factory)**

```python
from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, bcrypt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # 注册蓝图 — 后续模块逐步添加
    from .api import register_blueprints
    register_blueprints(app)

    return app
```

**Step 6: 创建 api/__init__.py (占位)**

```python
def register_blueprints(app):
    pass
```

**Step 7: 创建 run.py**

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

**Step 8: 安装依赖 & 验证启动**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Expected: Flask dev server 启动在 5000 端口

**Step 9: Commit**

```bash
git add backend/
git commit -m "chore: init backend Flask project scaffold"
```

---

## Task 2: 创建数据库 Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/role.py`
- Create: `backend/app/models/permission.py`
- Create: `backend/app/models/asset_param.py`
- Create: `backend/app/models/asset.py`
- Create: `backend/app/models/operation_log.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: 创建 role.py**

```python
from ..extensions import db

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    status = db.Column(db.String(16), default="active")  # active / disabled

    users = db.relationship("User", backref="role", lazy="dynamic")
    permissions = db.relationship(
        "Permission", secondary="role_permissions", backref="roles", lazy="dynamic"
    )

# 关联表
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)
```

**Step 2: 创建 permission.py**

```python
from ..extensions import db

class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))
    sort_order = db.Column(db.Integer, default=0)

    children = db.relationship("Permission", backref=db.backref("parent", remote_side=[id]), lazy="dynamic")
```

**Step 3: 创建 user.py**

```python
from ..extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    status = db.Column(db.String(16), default="active")  # active / disabled
```

**Step 4: 创建 asset_param.py**

```python
from ..extensions import db

class AssetParam(db.Model):
    __tablename__ = "asset_params"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), nullable=False, index=True)  # category/brand/unit/location/status
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(16), default="active")

    __table_args__ = (
        db.UniqueConstraint("type", "name", name="uq_asset_param_type_name"),
    )
```

**Step 5: 创建 asset.py**

```python
from datetime import datetime
from ..extensions import db

class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32))
    brand = db.Column(db.String(64))
    model = db.Column(db.String(64))
    serial_number = db.Column(db.String(64))
    unit = db.Column(db.String(16))
    purchase_date = db.Column(db.Date)
    location = db.Column(db.String(128))
    status = db.Column(db.String(16), default="idle")  # idle/distributed/borrowing/returned
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    borrower_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id], backref="owned_assets")
    borrower = db.relationship("User", foreign_keys=[borrower_id], backref="borrowed_assets")
```

**Step 6: 创建 operation_log.py**

```python
from datetime import datetime
from ..extensions import db

class OperationLog(db.Model):
    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(32), nullable=False)  # create/update/delete/distribute/borrow/return/revert/owner_change
    target_type = db.Column(db.String(32))  # user/role/asset/asset_param
    target_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="operation_logs")
```

**Step 7: 创建 flow_record.py**

```python
from datetime import datetime
from ..extensions import db

class FlowRecord(db.Model):
    __tablename__ = "flow_records"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    flow_type = db.Column(db.String(32), nullable=False)  # distribute/borrow/return/revert/owner_change
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    detail = db.Column(db.JSON)  # 存储流转时的所有字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    asset = db.relationship("Asset", backref="flow_records")
    operator = db.relationship("User")
```

**Step 8: 更新 models/__init__.py (导入所有模型)**

```python
from .role import Role, role_permissions
from .permission import Permission
from .user import User
from .asset_param import AssetParam
from .asset import Asset
from .operation_log import OperationLog
from .flow_record import FlowRecord
```

**Step 9: 初始化迁移**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/backend
source venv/bin/activate
flask db init
flask db migrate -m "initial tables"
flask db upgrade
```

Expected: 生成 `fams.db` 文件，包含全部表

**Step 10: Commit**

```bash
git add backend/
git commit -m "feat: add all database models with migrations"
```

---

## Task 3: 创建前端项目

**Files:**
- Create: `frontend/` (Vite 脚手架)

**Step 1: 用 Vite 创建 Vue 3 项目**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install element-plus vue-router@4 pinia axios
```

**Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
```

**Step 3: 创建目录结构**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/frontend
mkdir -p src/{router,stores,api,views,components,styles}
```

**Step 4: 创建 src/main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { size: 'default' })
app.mount('#app')
```

**Step 5: 创建 router/index.js (占位)**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

**Step 6: 创建 App.vue (最小)**

```vue
<template>
  <router-view />
</template>
```

**Step 7: 创建 views/Login.vue (占位)**

```vue
<template>
  <div class="login-page">
    <h1>固定资产管理系统</h1>
    <p>登录页 — 后续模块实现</p>
  </div>
</template>
```

**Step 8: 验证前端启动**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/frontend
npm run dev
```

Expected: Vite dev server 启动在 5173，页面显示"固定资产管理系统"

**Step 9: Commit**

```bash
git add frontend/
git commit -m "chore: init frontend Vue 3 project scaffold"
```

---

## ✅ 完成标准

- [ ] 后端 `python run.py` 启动无报错
- [ ] `flask db upgrade` 生成全部表
- [ ] 前端 `npm run dev` 启动无报错
- [ ] Vite proxy 配置指向 Flask 5000 端口
