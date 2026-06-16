"""
告警控制器
"""
from flask import Blueprint, request
from services.alert_service import AlertService
from middleware.auth_middleware import login_required

alert_bp = Blueprint('alert', __name__)


@alert_bp.route('/list', methods=['GET'])
@login_required
def get_alerts():
    """获取告警列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    severity = request.args.get('severity')
    status = request.args.get('status')
    equipment_id = request.args.get('equipmentId', type=int)

    return AlertService.get_alerts(page, size, severity, status, equipment_id)


@alert_bp.route('/<int:alert_id>', methods=['GET'])
@login_required
def get_alert(alert_id):
    """获取告警详情"""
    return AlertService.get_alert_by_id(alert_id)


@alert_bp.route('/', methods=['POST'])
@login_required
def create_alert():
    """创建告警"""
    data = request.get_json()
    return AlertService.create_alert(data)


@alert_bp.route('/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """确认告警"""
    data = request.get_json() or {}
    note = data.get('note')
    return AlertService.acknowledge_alert(alert_id, note)


@alert_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """解决告警"""
    data = request.get_json() or {}
    note = data.get('note')
    return AlertService.resolve_alert(alert_id, note)


@alert_bp.route('/batch-resolve', methods=['POST'])
@login_required
def batch_resolve():
    """批量解决告警"""
    data = request.get_json()
    alert_ids = data.get('alert_ids', [])
    note = data.get('note')
    return AlertService.batch_resolve(alert_ids, note)


@alert_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取告警统计"""
    return AlertService.get_alert_statistics()
