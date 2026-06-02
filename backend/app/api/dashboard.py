from flask import Blueprint, request, jsonify
from ..extensions import db
from sqlalchemy import func
from ..models.asset import Asset
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    total = Asset.query.count()
    idle = Asset.query.filter_by(status="idle").count()
    distributed = Asset.query.filter_by(status="distributed").count()
    borrowing = Asset.query.filter_by(status="borrowing").count()
    returned = Asset.query.filter_by(status="returned").count()
    return jsonify({
        "total": total, "idle": idle,
        "distributed": distributed, "borrowing": borrowing, "returned": returned,
    })


@dashboard_bp.route("/recent-assets", methods=["GET"])
@login_required
def recent_assets():
    assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    return jsonify({
        "items": [{
            "id": a.id, "code": a.code, "name": a.name,
            "category": a.category, "status": a.status,
            "owner_name": a.owner.name if a.owner else a.borrower.name if a.borrower else None,
            "updated_at": str(a.updated_at) if a.updated_at else None,
        } for a in assets]
    })
