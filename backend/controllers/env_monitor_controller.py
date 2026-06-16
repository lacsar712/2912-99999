"""
环境监测控制器
"""
from flask import Blueprint, request
from services.env_monitor_service import EnvMonitorService
from middleware.auth_middleware import login_required

env_monitor_bp = Blueprint('env_monitor', __name__)


# ==================== 区域管理 ====================

@env_monitor_bp.route('/areas/tree', methods=['GET'])
@login_required
def get_area_tree():
    return EnvMonitorService.get_area_tree()


@env_monitor_bp.route('/areas', methods=['GET'])
@login_required
def get_areas():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    parent_id = request.args.get('parentId', type=int)
    return EnvMonitorService.get_areas(page, size, parent_id)


@env_monitor_bp.route('/areas/<int:area_id>', methods=['GET'])
@login_required
def get_area(area_id):
    return EnvMonitorService.get_area_by_id(area_id)


@env_monitor_bp.route('/areas', methods=['POST'])
@login_required
def create_area():
    data = request.get_json()
    return EnvMonitorService.create_area(data)


@env_monitor_bp.route('/areas/<int:area_id>', methods=['PUT'])
@login_required
def update_area(area_id):
    data = request.get_json()
    return EnvMonitorService.update_area(area_id, data)


@env_monitor_bp.route('/areas/<int:area_id>', methods=['DELETE'])
@login_required
def delete_area(area_id):
    return EnvMonitorService.delete_area(area_id)


# ==================== 监测点管理 ====================

@env_monitor_bp.route('/points', methods=['GET'])
@login_required
def get_monitor_points():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    area_id = request.args.get('areaId', type=int)
    point_status = request.args.get('status')
    return EnvMonitorService.get_monitor_points(page, size, area_id, point_status)


@env_monitor_bp.route('/points/<int:point_id>', methods=['GET'])
@login_required
def get_monitor_point(point_id):
    return EnvMonitorService.get_monitor_point_by_id(point_id)


@env_monitor_bp.route('/points', methods=['POST'])
@login_required
def create_monitor_point():
    data = request.get_json()
    return EnvMonitorService.create_monitor_point(data)


@env_monitor_bp.route('/points/<int:point_id>', methods=['PUT'])
@login_required
def update_monitor_point(point_id):
    data = request.get_json()
    return EnvMonitorService.update_monitor_point(point_id, data)


@env_monitor_bp.route('/points/<int:point_id>', methods=['DELETE'])
@login_required
def delete_monitor_point(point_id):
    return EnvMonitorService.delete_monitor_point(point_id)


# ==================== 读数管理 ====================

@env_monitor_bp.route('/readings', methods=['POST'])
@login_required
def add_reading():
    data = request.get_json()
    return EnvMonitorService.add_reading(data)


@env_monitor_bp.route('/readings/batch', methods=['POST'])
@login_required
def batch_add_readings():
    data = request.get_json()
    return EnvMonitorService.batch_add_readings(data)


@env_monitor_bp.route('/readings/realtime', methods=['GET'])
@login_required
def get_realtime_readings():
    area_id = request.args.get('areaId', type=int)
    point_id = request.args.get('pointId', type=int)
    return EnvMonitorService.get_realtime_readings(area_id, point_id)


# ==================== 历史趋势 ====================

@env_monitor_bp.route('/readings/history', methods=['GET'])
@login_required
def get_history_trend():
    area_id = request.args.get('areaId', type=int)
    point_id = request.args.get('pointId', type=int)
    item_names = request.args.get('itemNames', '')
    time_window = request.args.get('timeWindow', '1h')
    
    item_names_list = [name.strip() for name in item_names.split(',') if name.strip()]
    
    if not area_id:
        from utils.response import Response
        return Response.bad_request('区域ID不能为空')
    if not item_names_list:
        from utils.response import Response
        return Response.bad_request('监测项目不能为空')
    
    return EnvMonitorService.get_history_trend(area_id, item_names_list, time_window, point_id)


# ==================== 环境标准管理 ====================

@env_monitor_bp.route('/standards', methods=['GET'])
@login_required
def get_standards():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    item_name = request.args.get('itemName')
    return EnvMonitorService.get_standards(page, size, item_name)


@env_monitor_bp.route('/standards/all', methods=['GET'])
@login_required
def get_all_standards():
    return EnvMonitorService.get_all_standards()


@env_monitor_bp.route('/standards/<int:standard_id>', methods=['GET'])
@login_required
def get_standard(standard_id):
    return EnvMonitorService.get_standard_by_id(standard_id)


@env_monitor_bp.route('/standards', methods=['POST'])
@login_required
def create_standard():
    data = request.get_json()
    return EnvMonitorService.create_standard(data)


@env_monitor_bp.route('/standards/<int:standard_id>', methods=['PUT'])
@login_required
def update_standard(standard_id):
    data = request.get_json()
    return EnvMonitorService.update_standard(standard_id, data)


@env_monitor_bp.route('/standards/<int:standard_id>', methods=['DELETE'])
@login_required
def delete_standard(standard_id):
    return EnvMonitorService.delete_standard(standard_id)


# ==================== 数据模拟 ====================

@env_monitor_bp.route('/simulate', methods=['POST'])
@login_required
def generate_simulated_readings():
    data = request.get_json()
    return EnvMonitorService.generate_simulated_readings(data)


# ==================== 统计数据 ====================

@env_monitor_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    return EnvMonitorService.get_statistics()
