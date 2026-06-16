"""
统一响应格式工具
"""
from flask import jsonify
from typing import Any, Optional, List


class Response:
    """API响应封装类"""

    @staticmethod
    def success(data: Any = None, message: str = '操作成功', code: int = 200):
        """成功响应"""
        return jsonify({
            'code': code,
            'message': message,
            'data': data
        }), code

    @staticmethod
    def error(message: str = '操作失败', code: int = 400, data: Any = None):
        """错误响应"""
        return jsonify({
            'code': code,
            'message': message,
            'data': data
        }), code

    @staticmethod
    def paginate(
        items: List[Any],
        total: int,
        page: int,
        size: int,
        message: str = '查询成功'
    ):
        """分页响应"""
        return jsonify({
            'code': 200,
            'message': message,
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size if size > 0 else 0
            }
        }), 200

    @staticmethod
    def created(data: Any = None, message: str = '创建成功'):
        """创建成功响应"""
        return Response.success(data, message, 201)

    @staticmethod
    def not_found(message: str = '资源不存在'):
        """未找到响应"""
        return Response.error(message, 404)

    @staticmethod
    def unauthorized(message: str = '未授权'):
        """未授权响应"""
        return Response.error(message, 401)

    @staticmethod
    def forbidden(message: str = '权限不足'):
        """禁止访问响应"""
        return Response.error(message, 403)

    @staticmethod
    def bad_request(message: str = '请求参数错误'):
        """错误请求响应"""
        return Response.error(message, 400)
