"""
数据服务
"""
from flask import g
from database.db import db
from models.data import Data
from models.log import Log
from utils.response import Response
from utils.validator import Validator


class DataService:
    """数据服务类"""

    @staticmethod
    def get_list(page=1, size=10, keyword=None, type=None, category_id=None, user_id=None):
        """
        获取数据列表

        Args:
            page: 页码
            size: 每页条数
            keyword: 搜索关键词
            type: 数据类型
            category_id: 分类ID
            user_id: 用户ID

        Returns:
            Response对象
        """
        query = Data.search(
            keyword=keyword,
            type=type,
            category_id=category_id,
            user_id=user_id
        )

        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )

        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total,
            page,
            size
        )

    @staticmethod
    def get_by_id(data_id):
        """
        根据ID获取数据

        Args:
            data_id: 数据ID

        Returns:
            Response对象
        """
        data = Data.get_by_id(data_id)
        if not data:
            return Response.not_found('数据不存在')

        return Response.success(data.to_dict())

    @staticmethod
    def create(data):
        """
        创建数据

        Args:
            data: 数据字典

        Returns:
            Response对象
        """
        # 验证必填字段
        validation = Validator.validate_form(data, {
            'name': ['required'],
            'type': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        # 清理输入
        data = Validator.sanitize_dict(data)

        # 创建数据
        new_data = Data(
            name=data.get('name'),
            type=data.get('type'),
            value=data.get('value'),
            description=data.get('description'),
            category_id=data.get('category_id'),
            user_id=g.user_id
        )

        try:
            new_data.save()

            Log.add_log(
                user_id=g.user_id,
                username=g.username,
                action='create',
                module='data',
                description=f'创建数据: {new_data.name}'
            )

            return Response.created({'id': new_data.id}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update(data_id, data):
        """
        更新数据

        Args:
            data_id: 数据ID
            data: 更新数据

        Returns:
            Response对象
        """
        existing = Data.get_by_id(data_id)
        if not existing:
            return Response.not_found('数据不存在')

        # 验证必填字段
        if 'name' in data and not data['name']:
            return Response.bad_request('名称不能为空')

        if 'type' in data and not data['type']:
            return Response.bad_request('类型不能为空')

        # 清理输入
        data = Validator.sanitize_dict(data)

        # 更新数据
        allowed_fields = ['name', 'type', 'value', 'description', 'category_id']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        existing.update(**update_data)

        Log.add_log(
            user_id=g.user_id,
            username=g.username,
            action='update',
            module='data',
            description=f'更新数据: {existing.name}'
        )

        return Response.success({'id': existing.id}, '更新成功')

    @staticmethod
    def delete(data_id):
        """
        删除数据

        Args:
            data_id: 数据ID

        Returns:
            Response对象
        """
        data = Data.get_by_id(data_id)
        if not data:
            return Response.not_found('数据不存在')

        data.delete()

        Log.add_log(
            user_id=g.user_id,
            username=g.username,
            action='delete',
            module='data',
            description=f'删除数据: {data.name}'
        )

        return Response.success(message='删除成功')

    @staticmethod
    def batch_delete(ids):
        """
        批量删除数据

        Args:
            ids: ID列表

        Returns:
            Response对象
        """
        if not ids:
            return Response.bad_request('请选择要删除的数据')

        count = 0
        for data_id in ids:
            data = Data.get_by_id(data_id)
            if data:
                data.delete()
                count += 1

        Log.add_log(
            user_id=g.user_id,
            username=g.username,
            action='batch_delete',
            module='data',
            description=f'批量删除数据: {count}条'
        )

        return Response.success({'count': count}, f'成功删除{count}条数据')

    @staticmethod
    def get_types():
        """
        获取所有数据类型

        Returns:
            Response对象
        """
        types = db.session.query(Data.type).filter(
            Data.status == 1
        ).distinct().all()

        return Response.success([t[0] for t in types])
