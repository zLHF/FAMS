from flask import Blueprint, request, jsonify
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

logs_bp = Blueprint("logs", __name__, url_prefix="/api/operation-logs")


@logs_bp.route("", methods=["GET"])
@login_required
def list_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    action = request.args.get("action", "")

    query = OperationLog.query.filter_by(tenant_id=request.current_tenant.id)
    if action:
        query = query.filter_by(action=action)

    pag = query.order_by(OperationLog.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [{
            "id": l.id, "user_name": l.user.name if l.user else "",
            "action": l.action, "target_type": l.target_type,
            "target_id": l.target_id, "detail": l.detail,
            "created_at": str(l.created_at) if l.created_at else None,
        } for l in pag.items],
        "total": pag.total, "page": pag.page, "per_page": pag.per_page,
    })
