"""
认证中间件
"""
from functools import wraps
from flask import request, g
from utils.jwt_helper import JWTHelper
from utils.response import Response


class AuthMiddleware:
    """认证中间件"""

    # 不需要认证的路径
    EXCLUDE_PATHS = [
        '/health',
        '/',
        '/api/auth/login',
        '/api/auth/register',
        '/api/auth/check-username',  # 用户名检查API不需要认证
    ]

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self._before_request)

    def _before_request(self):
        """请求前处理"""
        # 检查是否需要认证
        if request.path in self.EXCLUDE_PATHS:
            return

        # 检查是否是静态文件
        if request.path.startswith('/static'):
            return

        # 获取Token
        token = self._get_token()
        if not token:
            return Response.unauthorized('请先登录')

        # 验证Token
        result = JWTHelper.decode_token(token)
        if not result['valid']:
            return Response.unauthorized(result.get('message', 'Token无效'))

        # 存储用户信息到请求上下文
        g.user_id = result['data']['user_id']
        g.username = result['data']['username']
        g.user_role = result['data']['role']

    def _get_token(self):
        """获取Token - 仅从请求头获取，确保安全性"""
        # 从请求头获取 (推荐方式)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]

        return None


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user_id'):
            return Response.unauthorized('请先登录')
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user_id'):
            return Response.unauthorized('请先登录')

        if g.user_role != 'admin':
            return Response.forbidden('需要管理员权限')

        return f(*args, **kwargs)
    return decorated_function
