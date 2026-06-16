"""
系统配置控制器
"""
from flask import Blueprint, request, g

from models.config import Config as SystemConfig
from middleware.auth_middleware import admin_required
from utils.response import Response

config_bp = Blueprint('config', __name__)


@config_bp.route('', methods=['GET'])
@admin_required
def get_config():
    """获取系统配置（管理员）"""
    configs = SystemConfig.query.filter(SystemConfig.status == 1).all()
    result = {c.config_key: c.config_value for c in configs}
    return Response.success(result)


@config_bp.route('', methods=['PUT'])
@admin_required
def update_config():
    """更新系统配置（管理员）"""
    data = request.get_json()

    for key, value in data.items():
        SystemConfig.set_value(key, value)

    return Response.success(message='配置更新成功')


@config_bp.route('/<key>', methods=['GET'])
def get_config_value(key):
    """获取单个配置值"""
    value = SystemConfig.get_value(key)
    if value is None:
        return Response.not_found('配置项不存在')
    return Response.success({'key': key, 'value': value})


@config_bp.route('/<key>', methods=['PUT'])
@admin_required
def set_config_value(key):
    """设置单个配置值（管理员）"""
    data = request.get_json()
    value = data.get('value')
    config_type = data.get('type', 'string')
    description = data.get('description')

    SystemConfig.set_value(key, value, config_type, description)
    return Response.success(message='配置更新成功')
