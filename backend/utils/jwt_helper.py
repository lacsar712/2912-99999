"""
JWT Token 工具
"""
import jwt
import datetime
from typing import Dict, Optional, Any
from config import Config


class JWTHelper:
    """JWT工具类"""

    SECRET_KEY = Config.SECRET_KEY
    ALGORITHM = Config.JWT_ALGORITHM
    EXPIRE_HOURS = Config.JWT_EXPIRE_HOURS

    @classmethod
    def generate_token(cls, user_id: int, username: str, role: str) -> str:
        """生成Token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=cls.EXPIRE_HOURS),
            'iat': datetime.datetime.utcnow()
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """解析Token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return {'valid': True, 'data': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'message': 'Token已过期'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'message': '无效的Token'}

    @classmethod
    def get_user_id(cls, token: str) -> Optional[int]:
        """从Token获取用户ID"""
        result = cls.decode_token(token)
        if result['valid']:
            return result['data']['user_id']
        return None

    @classmethod
    def get_user_info(cls, token: str) -> Optional[Dict[str, Any]]:
        """从Token获取用户信息"""
        result = cls.decode_token(token)
        if result['valid']:
            return {
                'user_id': result['data']['user_id'],
                'username': result['data']['username'],
                'role': result['data']['role']
            }
        return None

    @classmethod
    def verify_admin(cls, token: str) -> bool:
        """验证是否为管理员"""
        result = cls.decode_token(token)
        if result['valid']:
            return result['data']['role'] == 'admin'
        return False
