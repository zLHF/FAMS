"""初始化种子数据 — 仅用于开发环境，请勿在生产环境运行"""
import os
import sys
from app import create_app
from app.extensions import db, bcrypt
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.asset_param import AssetParam
from app.models.asset import Asset


def seed():
    if os.environ.get("FLASK_ENV") == "production":
        print("ERROR: seed.py 不能在生产环境运行")
        sys.exit(1)
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 权限树
        perms_data = [
            {"name": "工作台", "code": "dashboard"},
            {"name": "人员管理", "code": "personnel"},
            {"name": "用户管理", "code": "users", "parent": "personnel"},
            {"name": "角色管理", "code": "roles", "parent": "personnel"},
            {"name": "权限管理", "code": "permissions", "parent": "personnel"},
            {"name": "基础参数设置", "code": "asset_params"},
            {"name": "固定资产管理", "code": "assets"},
            {"name": "资产台账", "code": "asset_list", "parent": "assets"},
            {"name": "资产派发", "code": "asset_distribute", "parent": "assets"},
            {"name": "资产借用", "code": "asset_borrow", "parent": "assets"},
            {"name": "借用归还", "code": "asset_return", "parent": "assets"},
            {"name": "领用退库", "code": "asset_revert", "parent": "assets"},
            {"name": "变更领用人", "code": "asset_owner_change", "parent": "assets"},
        ]
        perm_map = {}
        for p in perms_data:
            parent_obj = perm_map.get(p.get("parent"))
            obj = Permission(name=p["name"], code=p["code"], parent_id=parent_obj.id if parent_obj else None)
            db.session.add(obj)
            db.session.flush()
            perm_map[p["code"]] = obj

        # 角色
        admin_role = Role(name="系统管理员", code="admin", status="active")
        asset_role = Role(name="资产管理员", code="asset_manager", description="负责资产日常管理", status="active")
        db.session.add_all([admin_role, asset_role])
        db.session.flush()

        # 管理员全部权限
        from app.models.role import role_permissions
        for p in perm_map.values():
            db.session.execute(
                role_permissions.insert().values(role_id=admin_role.id, permission_id=p.id)
            )

        # 用户
        admin_user = User(
            username="admin",
            password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
            name="管理员", role_id=admin_role.id, status="active",
        )
        zhangsan = User(
            username="zhangsan",
            password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
            name="张三", department="研发部", role_id=asset_role.id, status="active",
        )
        lisi = User(
            username="lisi",
            password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
            name="李四", department="财务部", role_id=asset_role.id, status="active",
        )
        wangwu = User(
            username="wangwu",
            password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
            name="王五", department="市场部", role_id=asset_role.id, status="active",
        )
        db.session.add_all([admin_user, zhangsan, lisi, wangwu])
        db.session.flush()

        # 基础参数
        params_data = [
            ("category", "电脑设备", "computer"), ("category", "办公家具", "furniture"),
            ("category", "网络设备", "network"), ("category", "办公电器", "appliance"),
            ("brand", "联想", "lenovo"), ("brand", "戴尔", "dell"),
            ("brand", "惠普", "hp"), ("brand", "苹果", "apple"),
            ("unit", "台", "tai"), ("unit", "个", "ge"),
            ("unit", "套", "tao"), ("unit", "张", "zhang"),
            ("location", "总部库房", "hq_warehouse"), ("location", "财务部", "finance"),
            ("location", "研发部", "rd"), ("location", "会议室", "meeting"),
        ]
        for idx, (t, n, c) in enumerate(params_data):
            db.session.add(AssetParam(type=t, name=n, code=c, sort_order=idx, status="active"))

        # 示例资产
        assets_data = [
            {"code": "A001", "name": "联想ThinkPad X1", "category": "电脑设备", "brand": "联想", "model": "ThinkPad X1 Carbon", "unit": "台", "location": "研发部", "status": "distributed", "owner_id": zhangsan.id},
            {"code": "A002", "name": "戴尔U2720显示器", "category": "电脑设备", "brand": "戴尔", "model": "U2720Q", "unit": "台", "location": "研发部", "status": "distributed", "owner_id": zhangsan.id},
            {"code": "A003", "name": "办公桌(大)", "category": "办公家具", "brand": "", "unit": "张", "location": "财务部", "status": "distributed", "owner_id": lisi.id},
            {"code": "A004", "name": "思科交换机", "category": "网络设备", "brand": "思科", "model": "C9200", "unit": "台", "location": "总部库房", "status": "idle"},
            {"code": "A005", "name": "MacBook Pro 14", "category": "电脑设备", "brand": "苹果", "model": "M3 Pro", "unit": "台", "location": "总部库房", "status": "borrowing", "borrower_id": wangwu.id},
            {"code": "A006", "name": "HP LaserJet打印机", "category": "办公电器", "brand": "惠普", "model": "M404dn", "unit": "台", "location": "会议室", "status": "idle"},
            {"code": "A007", "name": "人体工学椅", "category": "办公家具", "brand": "", "unit": "把", "location": "总部库房", "status": "returned"},
            {"code": "A008", "name": "iPad Pro 12.9", "category": "电脑设备", "brand": "苹果", "model": "M2", "unit": "台", "location": "研发部", "status": "distributed", "owner_id": zhangsan.id},
        ]
        for ad in assets_data:
            owner_id = ad.pop("owner_id", None)
            borrower_id = ad.pop("borrower_id", None)
            a = Asset(**ad, owner_id=owner_id, borrower_id=borrower_id)
            db.session.add(a)

        db.session.commit()
        print("✅ 种子数据初始化完成")
        print(f"   用户: {User.query.count()} 条")
        print(f"   角色: {Role.query.count()} 条")
        print(f"   权限: {Permission.query.count()} 条")
        print(f"   参数: {AssetParam.query.count()} 条")
        print(f"   资产: {Asset.query.count()} 条")


if __name__ == "__main__":
    seed()
