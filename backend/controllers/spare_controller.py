"""
备件库存控制器
"""
from flask import Blueprint, request, g

from services.spare_service import (
    SparePartService, SpareInboundService, SpareOutboundService,
    SpareInventoryService, SpareStatisticsService
)
from middleware.auth_middleware import login_required

spare_bp = Blueprint('spare', __name__)


@spare_bp.route('/parts/equipment-types', methods=['GET'])
@login_required
def get_equipment_types():
    """获取设备类型列表"""
    return SparePartService.get_equipment_types()


@spare_bp.route('/parts/check-low-stock', methods=['POST'])
@login_required
def check_low_stock():
    """检查所有低库存并生成告警"""
    return SparePartService.check_all_low_stock()


@spare_bp.route('/parts', methods=['GET'])
@login_required
def get_parts():
    """获取备件列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    equipment_type = request.args.get('equipmentType')
    keyword = request.args.get('keyword')
    low_stock_only = request.args.get('lowStockOnly', 'false').lower() == 'true'

    return SparePartService.get_parts(page, size, equipment_type, keyword, low_stock_only)


@spare_bp.route('/parts/<int:part_id>', methods=['GET'])
@login_required
def get_part(part_id):
    """获取备件详情"""
    return SparePartService.get_part_by_id(part_id)


@spare_bp.route('/parts', methods=['POST'])
@login_required
def create_part():
    """创建备件"""
    data = request.get_json()
    return SparePartService.create_part(data)


@spare_bp.route('/parts/<int:part_id>', methods=['PUT'])
@login_required
def update_part(part_id):
    """更新备件"""
    data = request.get_json()
    return SparePartService.update_part(part_id, data)


@spare_bp.route('/parts/<int:part_id>', methods=['DELETE'])
@login_required
def delete_part(part_id):
    """删除备件"""
    return SparePartService.delete_part(part_id)


@spare_bp.route('/inbounds', methods=['GET'])
@login_required
def get_inbounds():
    """获取入库列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    part_id = request.args.get('partId', type=int)
    source_type = request.args.get('sourceType')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return SpareInboundService.get_inbounds(page, size, part_id, source_type, start_date, end_date)


@spare_bp.route('/inbounds', methods=['POST'])
@login_required
def create_inbound():
    """创建入库单"""
    data = request.get_json()
    return SpareInboundService.create_inbound(data)


@spare_bp.route('/inbounds/<int:inbound_id>', methods=['DELETE'])
@login_required
def delete_inbound(inbound_id):
    """删除入库单"""
    return SpareInboundService.delete_inbound(inbound_id)


@spare_bp.route('/outbounds', methods=['GET'])
@login_required
def get_outbounds():
    """获取领用列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    part_id = request.args.get('partId', type=int)
    work_order_id = request.args.get('workOrderId', type=int)
    is_returned = request.args.get('isReturned', type=int)
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return SpareOutboundService.get_outbounds(page, size, part_id, work_order_id, is_returned, start_date, end_date)


@spare_bp.route('/outbounds', methods=['POST'])
@login_required
def create_outbound():
    """创建领用单"""
    data = request.get_json()
    return SpareOutboundService.create_outbound(data)


@spare_bp.route('/outbounds/<int:outbound_id>/return', methods=['POST'])
@login_required
def return_outbound(outbound_id):
    """归还备件"""
    return SpareOutboundService.return_outbound(outbound_id)


@spare_bp.route('/outbounds/<int:outbound_id>', methods=['DELETE'])
@login_required
def delete_outbound(outbound_id):
    """删除领用单"""
    return SpareOutboundService.delete_outbound(outbound_id)


@spare_bp.route('/inventories/batch', methods=['POST'])
@login_required
def batch_create_inventory():
    """批量创建盘点单"""
    data = request.get_json()
    return SpareInventoryService.batch_create_inventory(data)


@spare_bp.route('/inventories', methods=['GET'])
@login_required
def get_inventories():
    """获取盘点列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    part_id = request.args.get('partId', type=int)
    inventory_month = request.args.get('inventoryMonth')
    has_difference = request.args.get('hasDifference', 'false').lower() == 'true'

    return SpareInventoryService.get_inventories(page, size, part_id, inventory_month, has_difference)


@spare_bp.route('/inventories', methods=['POST'])
@login_required
def create_inventory():
    """创建盘点单"""
    data = request.get_json()
    return SpareInventoryService.create_inventory(data)


@spare_bp.route('/inventories/<int:inventory_id>', methods=['PUT'])
@login_required
def update_inventory(inventory_id):
    """更新盘点单"""
    data = request.get_json()
    return SpareInventoryService.update_inventory(inventory_id, data)


@spare_bp.route('/inventories/<int:inventory_id>', methods=['DELETE'])
@login_required
def delete_inventory(inventory_id):
    """删除盘点单"""
    return SpareInventoryService.delete_inventory(inventory_id)


@spare_bp.route('/statistics/turnover', methods=['GET'])
@login_required
def get_turnover_rate():
    """获取周转率统计"""
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    top_n = request.args.get('topN', 10, type=int)

    return SpareStatisticsService.get_turnover_rate(start_date, end_date, top_n)


@spare_bp.route('/statistics/dashboard', methods=['GET'])
@login_required
def get_statistics_dashboard():
    """获取备件概览统计"""
    return SpareStatisticsService.get_dashboard()
