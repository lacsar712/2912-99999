"""
生产线监控控制器
"""
from flask import Blueprint, request, g

from services.production_service import (
    ProductionService, EquipmentService, SensorService,
    TaskService, StatisticsService
)
from middleware.auth_middleware import login_required

production_bp = Blueprint('production', __name__)


# ==================== 生产线接口 ====================

@production_bp.route('/lines', methods=['GET'])
@login_required
def get_lines():
    """获取生产线列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status')

    return ProductionService.get_lines(page, size, status)


@production_bp.route('/lines/<int:line_id>', methods=['GET'])
@login_required
def get_line(line_id):
    """获取生产线详情"""
    return ProductionService.get_line_by_id(line_id)


@production_bp.route('/lines', methods=['POST'])
@login_required
def create_line():
    """创建生产线"""
    data = request.get_json()
    return ProductionService.create_line(data)


@production_bp.route('/lines/<int:line_id>', methods=['PUT'])
@login_required
def update_line(line_id):
    """更新生产线"""
    data = request.get_json()
    return ProductionService.update_line(line_id, data)


@production_bp.route('/lines/<int:line_id>', methods=['DELETE'])
@login_required
def delete_line(line_id):
    """删除生产线"""
    return ProductionService.delete_line(line_id)


# ==================== 设备接口 ====================

@production_bp.route('/equipments', methods=['GET'])
@login_required
def get_equipments():
    """获取设备列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    line_id = request.args.get('lineId', type=int)
    status = request.args.get('status')

    return EquipmentService.get_equipments(page, size, line_id, status)


@production_bp.route('/equipments/<int:equipment_id>', methods=['GET'])
@login_required
def get_equipment(equipment_id):
    """获取设备详情"""
    return EquipmentService.get_equipment_by_id(equipment_id)


@production_bp.route('/equipments', methods=['POST'])
@login_required
def create_equipment():
    """创建设备"""
    data = request.get_json()
    return EquipmentService.create_equipment(data)


@production_bp.route('/equipments/<int:equipment_id>', methods=['PUT'])
@login_required
def update_equipment(equipment_id):
    """更新设备"""
    data = request.get_json()
    return EquipmentService.update_equipment(equipment_id, data)


@production_bp.route('/equipments/<int:equipment_id>/control', methods=['POST'])
@login_required
def control_equipment(equipment_id):
    """控制设备"""
    data = request.get_json()
    action = data.get('action')
    return EquipmentService.control_equipment(equipment_id, action)


# ==================== 传感器接口 ====================

@production_bp.route('/sensors', methods=['GET'])
@login_required
def get_sensors():
    """获取传感器列表"""
    equipment_id = request.args.get('equipmentId', type=int)
    status = request.args.get('status')

    return SensorService.get_sensors(equipment_id, status)


@production_bp.route('/sensors/realtime', methods=['GET'])
@login_required
def get_realtime_data():
    """获取实时传感器数据"""
    equipment_id = request.args.get('equipmentId', type=int)
    return SensorService.get_sensor_realtime_data(equipment_id)


# ==================== 任务接口 ====================

@production_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """获取任务列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    line_id = request.args.get('lineId', type=int)
    status = request.args.get('status')

    return TaskService.get_tasks(page, size, line_id, status)


@production_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    """创建任务"""
    data = request.get_json()
    return TaskService.create_task(data)


@production_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
@login_required
def update_task_status(task_id):
    """更新任务状态"""
    data = request.get_json()
    new_status = data.get('status')
    return TaskService.update_task_status(task_id, new_status)


# ==================== 统计接口 ====================

@production_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """获取仪表盘数据"""
    return StatisticsService.get_dashboard_data()


@production_bp.route('/trend', methods=['GET'])
@login_required
def get_trend():
    """获取运行趋势"""
    days = request.args.get('days', 7, type=int)
    return StatisticsService.get_equipment_trend(days)
