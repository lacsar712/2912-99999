"""
认证控制器
"""
from flask import Blueprint, request, g

from services.auth_service import AuthService
from middleware.auth_middleware import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    return AuthService.register(
        username=data.get('username'),
        password=data.get('password'),
        email=data.get('email')
    )


@auth_bp.route('/check-username', methods=['GET'])
def check_username():
    """检查用户名是否可用"""
    username = request.args.get('username', '').strip()
    return AuthService.check_username_availability(username)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    return AuthService.login(
        username=data.get('username'),
        password=data.get('password'),
        ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    return AuthService.logout()


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json()
    return AuthService.change_password(
        user_id=g.user_id,
        old_password=data.get('oldPassword'),
        new_password=data.get('newPassword')
    )
