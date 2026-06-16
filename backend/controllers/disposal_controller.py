"""
不合格品处置控制器
"""
from flask import Blueprint, request, g
from services.disposal_service import (
    DisposalOrderService, DisposalApprovalService, DisposalStatisticsService
)
from middleware.auth_middleware import login_required

disposal_bp = Blueprint('disposal', __name__)


@disposal_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """获取待处置单列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status')
    disposal_type = request.args.get('disposalType')
    source_type = request.args.get('sourceType')
    keyword = request.args.get('keyword')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    return DisposalOrderService.get_orders(
        page, size, status, disposal_type, source_type, keyword, start_date, end_date
    )


@disposal_bp.route('/orders/pending-approval', methods=['GET'])
@login_required
def get_my_pending_approvals():
    """获取我待审的列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    return DisposalOrderService.get_my_pending_approvals(page, size)


@disposal_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """获取待处置单详情"""
    return DisposalOrderService.get_order_by_id(order_id)


@disposal_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """创建待处置单"""
    data = request.get_json()
    return DisposalOrderService.create_order(data)


@disposal_bp.route('/orders/quick-create/<int:record_id>', methods=['POST'])
@login_required
def quick_create_from_quality(record_id):
    """从质检不合格记录快速创建"""
    data = request.get_json() or {}
    return DisposalOrderService.quick_create_from_quality(record_id, data)


@disposal_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    """更新待处置单"""
    data = request.get_json()
    return DisposalOrderService.update_order(order_id, data)


@disposal_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    """删除待处置单"""
    return DisposalOrderService.delete_order(order_id)


@disposal_bp.route('/orders/<int:order_id>/submit', methods=['POST'])
@login_required
def submit_order(order_id):
    """提交审批"""
    return DisposalOrderService.submit_order(order_id)


@disposal_bp.route('/orders/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_order(order_id):
    """审批通过"""
    data = request.get_json() or {}
    return DisposalApprovalService.approve_order(order_id, data)


@disposal_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    """审批驳回"""
    data = request.get_json() or {}
    return DisposalApprovalService.reject_order(order_id, data)


@disposal_bp.route('/orders/<int:order_id>/return', methods=['POST'])
@login_required
def return_order(order_id):
    """审批退回"""
    data = request.get_json() or {}
    return DisposalApprovalService.return_order(order_id, data)


@disposal_bp.route('/orders/<int:order_id>/result', methods=['POST'])
@login_required
def record_disposal_result(order_id):
    """记录处置结果"""
    data = request.get_json()
    return DisposalApprovalService.record_disposal_result(order_id, data)


@disposal_bp.route('/statistics/monthly', methods=['GET'])
@login_required
def get_monthly_statistics():
    """获取月度统计"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return DisposalStatisticsService.get_monthly_statistics(year, month)


@disposal_bp.route('/statistics/trend', methods=['GET'])
@login_required
def get_trend_statistics():
    """获取趋势统计"""
    months = request.args.get('months', 6, type=int)
    return DisposalStatisticsService.get_trend_statistics(months)


@disposal_bp.route('/statistics/dashboard', methods=['GET'])
@login_required
def get_statistics_dashboard():
    """获取统计概览"""
    return DisposalStatisticsService.get_dashboard()
