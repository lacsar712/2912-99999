"""
维修工单控制器
"""
from flask import Blueprint, request, g

from services.maintenance_service import MaintenanceService
from middleware.auth_middleware import login_required

maintenance_bp = Blueprint('maintenance', __name__)


@maintenance_bp.route('/work-orders', methods=['GET'])
@login_required
def get_work_orders():
    """获取维修工单列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status')
    equipment_id = request.args.get('equipmentId', type=int)
    priority = request.args.get('priority')

    return MaintenanceService.get_work_orders(page, size, status, equipment_id, priority)


@maintenance_bp.route('/work-orders/<int:order_id>', methods=['GET'])
@login_required
def get_work_order(order_id):
    """获取维修工单详情"""
    return MaintenanceService.get_work_order_by_id(order_id)


@maintenance_bp.route('/work-orders', methods=['POST'])
@login_required
def create_work_order():
    """创建维修工单"""
    data = request.get_json()
    return MaintenanceService.create_work_order(data)


@maintenance_bp.route('/work-orders/<int:order_id>', methods=['PUT'])
@login_required
def update_work_order(order_id):
    """更新维修工单"""
    data = request.get_json()
    return MaintenanceService.update_work_order(order_id, data)


@maintenance_bp.route('/work-orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    """更新工单状态"""
    data = request.get_json()
    status = data.get('status')
    return MaintenanceService.update_order_status(order_id, status)


@maintenance_bp.route('/work-orders/<int:order_id>', methods=['DELETE'])
@login_required
def delete_work_order(order_id):
    """删除维修工单"""
    return MaintenanceService.delete_work_order(order_id)


@maintenance_bp.route('/work-orders/statistics', methods=['GET'])
@login_required
def get_work_order_statistics():
    """获取工单统计"""
    return MaintenanceService.get_work_order_statistics()
