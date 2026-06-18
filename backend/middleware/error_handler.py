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

        degraded = self._check_degraded_response(e)
        if degraded is not None:
            return degraded

        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500

    def _check_degraded_response(self, e):
        """检查是否为依赖组件不可用导致的异常，返回降级提示"""
        error_msg = str(e).lower()
        error_type = type(e).__name__

        db_keywords = [
            "can't connect", "connection refused", "lost connection",
            "mysql", "pymysql", "sqlalchemy", "operationalerror",
            "2003", "2006", "2013",
        ]
        is_db_error = any(kw in error_msg or kw in error_type.lower() for kw in db_keywords)

        redis_keywords = ["redis", "connectionrefusederror", "max retries"]
        is_redis_error = any(kw in error_msg or kw in error_type.lower() for kw in redis_keywords)

        if is_db_error:
            try:
                from services.resilience import DegradationManager, SelfHealLog
                dm = DegradationManager.get_instance()
                if not dm.is_database_available():
                    SelfHealLog.append("database", "request_blocked", "write request blocked due to database down")
                    return jsonify({
                        'code': 503,
                        'message': '数据库暂不可用，系统当前处于降级模式，仅支持只读查询。请稍后重试。',
                        'data': {'degraded': True, 'component': 'database', 'mode': 'read_only'}
                    }), 503
            except Exception:
                pass

        if is_redis_error:
            try:
                from services.resilience import DegradationManager, SelfHealLog
                dm = DegradationManager.get_instance()
                if not dm.is_redis_available():
                    SelfHealLog.append("redis", "request_blocked", "request blocked due to redis down")
                    return jsonify({
                        'code': 503,
                        'message': '缓存服务暂不可用，部分限流功能降级。请稍后重试。',
                        'data': {'degraded': True, 'component': 'redis', 'mode': 'bypass_cache'}
                    }), 503
            except Exception:
                pass

        return None
