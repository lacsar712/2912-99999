"""
数据控制器
"""
from flask import Blueprint, request, g

from services.data_service import DataService
from middleware.auth_middleware import login_required

data_bp = Blueprint('data', __name__)


@data_bp.route('', methods=['GET'])
@login_required
def get_list():
    """获取数据列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword')
    data_type = request.args.get('type')
    category_id = request.args.get('categoryId', type=int)

    return DataService.get_list(
        page=page,
        size=size,
        keyword=keyword,
        type=data_type,
        category_id=category_id
    )


@data_bp.route('/<int:data_id>', methods=['GET'])
@login_required
def get_by_id(data_id):
    """根据ID获取数据"""
    return DataService.get_by_id(data_id)


@data_bp.route('', methods=['POST'])
@login_required
def create():
    """创建数据"""
    data = request.get_json()
    return DataService.create(data)


@data_bp.route('/<int:data_id>', methods=['PUT'])
@login_required
def update(data_id):
    """更新数据"""
    data = request.get_json()
    return DataService.update(data_id, data)


@data_bp.route('/<int:data_id>', methods=['DELETE'])
@login_required
def delete(data_id):
    """删除数据"""
    return DataService.delete(data_id)


@data_bp.route('/batch', methods=['DELETE'])
@login_required
def batch_delete():
    """批量删除数据"""
    data = request.get_json()
    ids = data.get('ids', [])
    return DataService.batch_delete(ids)


@data_bp.route('/types', methods=['GET'])
@login_required
def get_types():
    """获取所有数据类型"""
    return DataService.get_types()
