"""
成本核算控制器
"""
from flask import Blueprint, request, g

from services.cost_service import (
    CostElementService, CostRecordService, CostReportService
)
from middleware.auth_middleware import login_required

cost_bp = Blueprint('cost', __name__)


# ==================== 成本要素字典接口 ====================

@cost_bp.route('/elements', methods=['GET'])
@login_required
def get_elements():
    """获取成本要素列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    element_type = request.args.get('elementType')
    keyword = request.args.get('keyword')

    return CostElementService.get_elements(page, size, element_type, keyword)


@cost_bp.route('/elements/all', methods=['GET'])
@login_required
def get_all_elements():
    """获取所有可用成本要素（下拉选择用）"""
    return CostElementService.get_all_elements()


@cost_bp.route('/elements/<int:element_id>', methods=['GET'])
@login_required
def get_element(element_id):
    """获取成本要素详情"""
    return CostElementService.get_element_by_id(element_id)


@cost_bp.route('/elements', methods=['POST'])
@login_required
def create_element():
    """创建成本要素"""
    data = request.get_json()
    return CostElementService.create_element(data)


@cost_bp.route('/elements/<int:element_id>', methods=['PUT'])
@login_required
def update_element(element_id):
    """更新成本要素"""
    data = request.get_json()
    return CostElementService.update_element(element_id, data)


@cost_bp.route('/elements/<int:element_id>', methods=['DELETE'])
@login_required
def delete_element(element_id):
    """删除成本要素"""
    return CostElementService.delete_element(element_id)


@cost_bp.route('/elements/init-defaults', methods=['POST'])
@login_required
def init_default_elements():
    """初始化默认成本要素"""
    return CostElementService.init_default_elements()


# ==================== 成本登记接口 ====================

@cost_bp.route('/records', methods=['GET'])
@login_required
def get_records():
    """获取成本登记列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    task_id = request.args.get('taskId', type=int)
    element_id = request.args.get('elementId', type=int)
    element_type = request.args.get('elementType')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return CostRecordService.get_records(
        page, size, task_id, element_id, element_type, start_date, end_date
    )


@cost_bp.route('/records/<int:record_id>', methods=['GET'])
@login_required
def get_record(record_id):
    """获取成本登记详情"""
    return CostRecordService.get_record_by_id(record_id)


@cost_bp.route('/records', methods=['POST'])
@login_required
def create_record():
    """创建成本登记"""
    data = request.get_json()
    return CostRecordService.create_record(data)


@cost_bp.route('/records/batch', methods=['POST'])
@login_required
def batch_create_records():
    """批量创建成本登记"""
    data = request.get_json()
    return CostRecordService.batch_create_records(data)


@cost_bp.route('/records/<int:record_id>', methods=['PUT'])
@login_required
def update_record(record_id):
    """更新成本登记"""
    data = request.get_json()
    return CostRecordService.update_record(record_id, data)


@cost_bp.route('/records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(record_id):
    """删除成本登记"""
    return CostRecordService.delete_record(record_id)


@cost_bp.route('/tasks/<int:task_id>/calculate-cost', methods=['POST'])
@login_required
def calculate_task_cost(task_id):
    """任务完成自动初算成本"""
    return CostRecordService.calculate_task_cost(task_id)


@cost_bp.route('/tasks/<int:task_id>/cost', methods=['GET'])
@login_required
def get_task_cost(task_id):
    """获取任务成本详情"""
    return CostRecordService.get_task_cost(task_id)


# ==================== 成本报表接口 ====================

@cost_bp.route('/report/multi-dimension', methods=['GET'])
@login_required
def get_multi_dimension_report():
    """多维度成本分析报表"""
    dimension = request.args.get('dimension', 'product')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return CostReportService.get_multi_dimension_report(dimension, start_date, end_date)


@cost_bp.route('/report/monthly-summary', methods=['GET'])
@login_required
def get_monthly_summary():
    """按月汇总成本（含同比环比）"""
    months = request.args.get('months', 12, type=int)
    return CostReportService.get_monthly_summary(months)


@cost_bp.route('/report/dashboard-cost', methods=['GET'])
@login_required
def get_dashboard_cost():
    """获取仪表盘成本数据"""
    return CostReportService.get_dashboard_cost()


@cost_bp.route('/report/export-csv', methods=['GET'])
@login_required
def export_csv():
    """导出成本报表CSV"""
    dimension = request.args.get('dimension', 'product')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return CostReportService.export_csv(dimension, start_date, end_date)
