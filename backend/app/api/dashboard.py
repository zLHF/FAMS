from flask import Blueprint, request, jsonify
from ..models.asset import Asset
from ..models.flow_record import FlowRecord
from ..utils.decorators import login_required
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _current_tenant_id():
    tenant = getattr(request, "current_tenant", None)
    return tenant.id if tenant else None


@dashboard_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    tid = _current_tenant_id()
    if tid is None:
        return jsonify({"total": 0, "idle": 0, "distributed": 0, "borrowing": 0, "returned": 0})
    total = Asset.query.filter_by(tenant_id=tid).count()
    idle = Asset.query.filter_by(tenant_id=tid, status="idle").count()
    distributed = Asset.query.filter_by(tenant_id=tid, status="distributed").count()
    borrowing = Asset.query.filter_by(tenant_id=tid, status="borrowing").count()
    returned = Asset.query.filter_by(tenant_id=tid, status="returned").count()
    return jsonify({
        "total": total, "idle": idle,
        "distributed": distributed, "borrowing": borrowing, "returned": returned,
    })


@dashboard_bp.route("/recent-assets", methods=["GET"])
@login_required
def recent_assets():
    tid = _current_tenant_id()
    if tid is None:
        return jsonify({"items": []})
    assets = Asset.query.filter_by(tenant_id=tid).order_by(Asset.id.desc()).limit(5).all()
    return jsonify({
        "items": [{
            "id": a.id, "code": a.code, "name": a.name,
            "category": a.category, "status": a.status,
            "owner_name": a.owner.name if a.owner else a.borrower.name if a.borrower else None,
            "updated_at": str(a.updated_at) if a.updated_at else None,
        } for a in assets]
    })


@dashboard_bp.route("/pending", methods=["GET"])
@login_required
def pending():
    """返回待处理事项"""
    tid = _current_tenant_id()
    if tid is None:
        return jsonify({"overdue_borrows": [], "recent_today": []})

    # 逾期借用
    overdue = FlowRecord.query.filter(
        FlowRecord.tenant_id == tid,
        FlowRecord.flow_type == "borrow",
        FlowRecord.detail["expected_return_date"].as_string() < str(date.today())
    ).all()

    # 获取逾期借用中的资产
    overdue_assets = []
    for record in overdue:
        asset = Asset.query.filter_by(id=record.asset_id, tenant_id=tid).first()
        if asset and asset.status == "borrowing":
            overdue_assets.append({
                "id": asset.id, "code": asset.code, "name": asset.name,
                "borrower_name": asset.borrower.name if asset.borrower else None,
                "expected_return": record.detail.get("expected_return_date", "") if record.detail else "",
            })

    # 今日新增资产
    today = str(date.today())
    recent = Asset.query.filter(
        Asset.tenant_id == tid,
        Asset.created_at.like(f"{today}%")
    ).order_by(Asset.id.desc()).limit(5).all()

    return jsonify({
        "overdue_borrows": overdue_assets,
        "recent_today": [{
            "id": a.id, "code": a.code, "name": a.name,
            "category": a.category, "status": a.status,
        } for a in recent],
    })
