"""
用户控制器
"""
from flask import Blueprint, request, g

from services.user_service import UserService
from middleware.auth_middleware import login_required, admin_required

user_bp = Blueprint('user', __name__)


@user_bp.route('/info', methods=['GET'])
@login_required
def get_user_info():
    """获取当前用户信息"""
    return UserService.get_user_info(g.user_id)


@user_bp.route('/info', methods=['PUT'])
@login_required
def update_user_info():
    """更新当前用户信息"""
    data = request.get_json()
    return UserService.update_user_info(g.user_id, data)


@user_bp.route('/list', methods=['GET'])
@admin_required
def get_user_list():
    """获取用户列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword')

    return UserService.get_user_list(page, size, keyword)


@user_bp.route('/<int:user_id>', methods=['GET'])
@admin_required
def get_user_by_id(user_id):
    """获取指定用户信息（管理员）"""
    return UserService.get_user_info(user_id)


@user_bp.route('/<int:user_id>/disable', methods=['POST'])
@admin_required
def disable_user(user_id):
    """禁用用户（管理员）"""
    return UserService.disable_user(user_id)


@user_bp.route('/<int:user_id>/enable', methods=['POST'])
@admin_required
def enable_user(user_id):
    """启用用户（管理员）"""
    return UserService.enable_user(user_id)
