"""
错误处理中间件
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException
from utils.logger import logger


class ErrorHandler:
    """错误处理中间件"""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化中间件"""
        app.errorhandler(400)(self._handle_bad_request)
        app.errorhandler(401)(self._handle_unauthorized)
        app.errorhandler(403)(self._handle_forbidden)
        app.errorhandler(404)(self._handle_not_found)
        app.errorhandler(500)(self._handle_internal_error)
        app.errorhandler(Exception)(self._handle_exception)

    def _handle_bad_request(self, e):
        """处理400错误"""
        logger.warning(f"Bad Request: {str(e)}")
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None
        }), 400

    def _handle_unauthorized(self, e):
        """处理401错误"""
        logger.warning(f"Unauthorized: {str(e)}")
        return jsonify({
            'code': 401,
            'message': '未授权访问',
            'data': None
        }), 401

    def _handle_forbidden(self, e):
        """处理403错误"""
        logger.warning(f"Forbidden: {str(e)}")
        return jsonify({
            'code': 403,
            'message': '权限不足',
            'data': None
        }), 403

    def _handle_not_found(self, e):
        """处理404错误"""
        logger.warning(f"Not Found: {str(e)}")
        return jsonify({
            'code': 404,
            'message': '请求的资源不存在',
            'data': None
        }), 404

    def _handle_internal_error(self, e):
        """处理500错误"""
        logger.error(f"Internal Error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500

    def _handle_exception(self, e):
        """处理其他异常"""
        logger.exception(f"Unexpected Exception: {str(e)}")

        if isinstance(e, HTTPException):
            return jsonify({
                'code': e.code,
                'message': e.description,
                'data': None
            }), e.code

        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
