"""
认证服务
"""
from flask import g
from database.db import db
from models.user import User
from models.log import Log
from utils.password_helper import PasswordHelper
from utils.jwt_helper import JWTHelper
from utils.response import Response
from utils.validator import Validator


class AuthService:
    """认证服务类"""

    @staticmethod
    def check_username_availability(username):
        """
        检查用户名是否可用

        Args:
            username: 用户名

        Returns:
            Response对象
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 清理用户名
        username = Validator.sanitize_string(username.strip() if username else '')
        
        # 验证用户名长度
        if not username:
            return Response.success({'available': False, 'message': '用户名不能为空'})
        
        if len(username) < 3:
            return Response.success({'available': False, 'message': '用户名至少3位'})
        
        if len(username) > 50:
            return Response.success({'available': False, 'message': '用户名最多50位'})
        
        # 验证用户名格式
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return Response.success({'available': False, 'message': '用户名只能包含字母、数字和下划线'})
        
        # 检查用户名是否存在
        existing_user = User.get_by_username(username)
        if existing_user:
            logger.info(f'用户名检查: {username} 已被占用')
            return Response.success({'available': False, 'message': '用户名已被占用'})
        
        logger.info(f'用户名检查: {username} 可用')
        return Response.success({'available': True, 'message': '用户名可用'})

    @staticmethod
    def register(username, password, email=None):
        """
        用户注册

        Args:
            username: 用户名
            password: 密码
            email: 邮箱

        Returns:
            Response对象
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 清理输入数据
        username = Validator.sanitize_string(username.strip() if username else '')
        password = password.strip() if password else ''
        email = Validator.sanitize_string(email.strip() if email else '') if email else None
        
        logger.info(f'注册请求: username={username}, email={email}')
        
        # 验证必填字段
        validation = Validator.validate_form({
            'username': username,
            'password': password
        }, {
            'username': ['required', {'name': 'min_length', 'param': 3}, {'name': 'max_length', 'param': 50}],
            'password': ['required', {'name': 'min_length', 'param': 6}, {'name': 'max_length', 'param': 100}]
        })

        if not validation['valid']:
            error_msg = list(validation['errors'].values())[0]
            logger.warning(f'注册验证失败: {error_msg}')
            return Response.bad_request(error_msg)
        
        # 验证用户名格式（只允许字母、数字、下划线）
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            logger.warning(f'注册用户名格式错误: {username}')
            return Response.bad_request('用户名只能包含字母、数字和下划线')

        # 验证邮箱格式（如果提供）
        if email:
            email_validation = Validator.validate_field(email, ['email'])
            if not email_validation['valid']:
                logger.warning(f'注册邮箱格式错误: {email}')
                return Response.bad_request(email_validation['message'])

        # 检查用户名是否存在
        existing_user = User.get_by_username(username)
        if existing_user:
            logger.warning(f'注册用户名已存在: {username}')
            return Response.error('用户名已存在', 409)

        # 检查邮箱是否存在
        if email:
            existing_email = User.get_by_email(email)
            if existing_email:
                logger.warning(f'注册邮箱已被使用: {email}')
                return Response.error('邮箱已被注册', 409)

        # 加密密码
        try:
            hashed_password = PasswordHelper.hash_password(password)
        except Exception as e:
            logger.error(f'密码加密失败: {str(e)}')
            return Response.error('系统错误，请稍后重试', 500)

        # 创建用户
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            role='user'
        )

        try:
            user.save()
            logger.info(f'用户注册成功: userId={user.id}, username={username}')
            return Response.created({'userId': user.id}, '注册成功')
        except Exception as e:
            db.session.rollback()
            logger.error(f'用户保存失败: {str(e)}', exc_info=True)
            return Response.error(f'注册失败，请稍后重试', 500)

    @staticmethod
    def login(username, password, ip=None, user_agent=None):
        """
        用户登录

        Args:
            username: 用户名
            password: 密码
            ip: IP地址
            user_agent: 用户代理

        Returns:
            Response对象
        """
        # 验证必填字段
        validation = Validator.validate_form({
            'username': username,
            'password': password
        }, {
            'username': ['required'],
            'password': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        # 查询用户
        user = User.get_by_username(username)

        if not user:
            return Response.not_found('用户不存在')

        # 检查状态
        if user.status != 1:
            return Response.error('账号已被禁用', 403)

        # 验证密码
        if not PasswordHelper.verify_password(password, user.password):
            return Response.error('密码错误', 401)

        # 生成Token
        token = JWTHelper.generate_token(user.id, user.username, user.role)

        # 记录登录日志
        Log.add_log(
            user_id=user.id,
            username=user.username,
            action='login',
            module='auth',
            description='用户登录',
            ip=ip,
            user_agent=user_agent
        )

        return Response.success({
            'token': token,
            'userInfo': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'createTime': user.create_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, '登录成功')

    @staticmethod
    def logout():
        """
        用户登出

        Returns:
            Response对象
        """
        # 记录登出日志
        if hasattr(g, 'user_id'):
            Log.add_log(
                user_id=g.user_id,
                username=g.username,
                action='logout',
                module='auth',
                description='用户登出'
            )

        return Response.success(message='登出成功')

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 原密码
            new_password: 新密码

        Returns:
            Response对象
        """
        # 验证新密码
        validation = Validator.validate_field(new_password, [
            'required',
            {'name': 'min_length', 'param': 6}
        ])

        if not validation['valid']:
            return Response.bad_request(validation['message'])

        # 查询用户
        user = User.get_by_id(user_id)
        if not user:
            return Response.not_found('用户不存在')

        # 验证原密码
        if not PasswordHelper.verify_password(old_password, user.password):
            return Response.error('原密码错误', 401)

        # 更新密码
        user.password = PasswordHelper.hash_password(new_password)
        user.save()

        return Response.success(message='密码修改成功')
