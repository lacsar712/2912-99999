"""
统计控制器
"""
from flask import Blueprint, request

from services.statistics_service import StatisticsService
from middleware.auth_middleware import login_required, admin_required

stats_bp = Blueprint('statistics', __name__)


@stats_bp.route('/overview', methods=['GET'])
@login_required
def get_overview():
    """获取统计概览"""
    return StatisticsService.get_overview()


@stats_bp.route('/type', methods=['GET'])
@login_required
def get_type_statistics():
    """获取类型统计"""
    return StatisticsService.get_type_statistics()


@stats_bp.route('/user', methods=['GET'])
@admin_required
def get_user_statistics():
    """获取用户统计（管理员）"""
    return StatisticsService.get_user_statistics()


@stats_bp.route('/log', methods=['GET'])
@admin_required
def get_operation_log():
    """获取操作日志（管理员）"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    user_id = request.args.get('userId', type=int)
    action = request.args.get('action')

    return StatisticsService.get_operation_log(
        page=page,
        size=size,
        user_id=user_id,
        action=action
    )
