"""
密码加密工具
"""
import bcrypt
from typing import Union


class PasswordHelper:
    """密码加密工具类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        密码加密

        Args:
            password: 明文密码

        Returns:
            加密后的密码字符串
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        密码验证

        Args:
            password: 明文密码
            hashed: 加密后的密码

        Returns:
            验证结果
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )

    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        验证密码强度

        Args:
            password: 明文密码

        Returns:
            验证结果字典
        """
        errors = []

        if len(password) < 6:
            errors.append('密码长度至少6位')

        if not any(c.isalpha() for c in password):
            errors.append('密码必须包含字母')

        if not any(c.isdigit() for c in password):
            errors.append('密码必须包含数字')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
