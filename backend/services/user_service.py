"""
用户服务
"""
from flask import g
from database.db import db
from models.user import User
from models.log import Log
from utils.response import Response
from utils.validator import Validator
from utils.password_helper import PasswordHelper


class UserService:
    """用户服务类"""

    @staticmethod
    def get_user_info(user_id):
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Response对象
        """
        user = User.get_by_id(user_id)
        if not user:
            return Response.not_found('用户不存在')

        return Response.success(user.to_dict())

    @staticmethod
    def update_user_info(user_id, data):
        """
        更新用户信息

        Args:
            user_id: 用户ID
            data: 更新数据

        Returns:
            Response对象
        """
        user = User.get_by_id(user_id)
        if not user:
            return Response.not_found('用户不存在')

        # 只允许更新特定字段
        allowed_fields = ['email']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        # 验证邮箱
        if 'email' in update_data and update_data['email']:
            if not Validator.validate_field(update_data['email'], ['email'])['valid']:
                return Response.bad_request('邮箱格式不正确')

            # 检查邮箱是否被其他用户使用
            existing = User.get_by_email(update_data['email'])
            if existing and existing.id != user_id:
                return Response.error('邮箱已被使用', 409)

        # 更新用户
        user.update(**update_data)

        return Response.success(user.to_dict(), '更新成功')

    @staticmethod
    def get_user_list(page=1, size=10, keyword=None):
        """
        获取用户列表

        Args:
            page: 页码
            size: 每页条数
            keyword: 搜索关键词

        Returns:
            Response对象
        """
        query = User.query.filter(User.status == 1)

        if keyword:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{keyword}%'),
                    User.email.like(f'%{keyword}%')
                )
            )

        pagination = query.order_by(User.create_time.desc()).paginate(
            page=page,
            per_page=size,
            error_out=False
        )

        return Response.paginate(
            [user.to_dict() for user in pagination.items],
            pagination.total,
            page,
            size
        )

    @staticmethod
    def disable_user(user_id):
        """
        禁用用户

        Args:
            user_id: 用户ID

        Returns:
            Response对象
        """
        user = User.get_by_id(user_id)
        if not user:
            return Response.not_found('用户不存在')

        user.status = 0
        user.save()

        Log.add_log(
            user_id=g.get('user_id'),
            username=g.get('username'),
            action='disable_user',
            module='user',
            description=f'禁用用户: {user.username}'
        )

        return Response.success(message='用户已禁用')

    @staticmethod
    def enable_user(user_id):
        """
        启用用户

        Args:
            user_id: 用户ID

        Returns:
            Response对象
        """
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return Response.not_found('用户不存在')

        user.status = 1
        user.save()

        Log.add_log(
            user_id=g.get('user_id'),
            username=g.get('username'),
            action='enable_user',
            module='user',
            description=f'启用用户: {user.username}'
        )

        return Response.success(message='用户已启用')
