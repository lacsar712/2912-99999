"""
系统健康状态控制器
提供容器编排探针与前端面板数据
"""
from flask import Blueprint, jsonify

from services.resilience import ComponentHealthChecker, DegradationManager, SelfHealLog
from middleware.auth_middleware import login_required

health_bp = Blueprint("health", __name__)


@health_bp.route("", methods=["GET"])
def full_health():
    result = ComponentHealthChecker.check_all()
    dm = DegradationManager.get_instance()
    result["degradation"] = dm.get_degradation_info()
    result["self_heal_log"] = SelfHealLog.recent(20)
    code = 200 if result["status"] == "healthy" else (503 if result["status"] == "unhealthy" else 200)
    return jsonify(result), code


@health_bp.route("/live", methods=["GET"])
def liveness():
    return jsonify({"status": "alive"}), 200


@health_bp.route("/ready", methods=["GET"])
def readiness():
    db_result = ComponentHealthChecker.check_database()
    if db_result["status"] == "unhealthy":
        return jsonify({"status": "not_ready", "reason": "database unavailable"}), 503
    return jsonify({"status": "ready"}), 200


@health_bp.route("/components", methods=["GET"])
@login_required
def component_detail():
    result = ComponentHealthChecker.check_all()
    dm = DegradationManager.get_instance()
    return jsonify({
        "code": 200,
        "data": {
            "components": result["components"],
            "degradation": dm.get_degradation_info(),
        },
    })


@health_bp.route("/heal-log", methods=["GET"])
@login_required
def heal_log():
    limit = 50
    records = SelfHealLog.recent(limit)
    return jsonify({
        "code": 200,
        "data": {
            "records": records,
            "total": len(records),
        },
    })
