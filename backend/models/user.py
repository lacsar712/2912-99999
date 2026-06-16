"""
用户模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = 't_user'

    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码(加密)')
    email = db.Column(db.String(100), comment='邮箱')
    role = db.Column(db.String(20), default='user', comment='角色: admin/user')

    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        # 移除敏感信息
        result.pop('password', None)
        return result

    def to_simple_dict(self):
        """简化字典（用于关联查询）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }

    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户"""
        return User.query.filter(
            User.username == username,
            User.status == 1
        ).first()

    @staticmethod
    def get_by_email(email):
        """根据邮箱获取用户"""
        return User.query.filter(
            User.email == email,
            User.status == 1
        ).first()

    def __repr__(self):
        return f'<User {self.username}>'
