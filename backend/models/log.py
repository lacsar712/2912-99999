"""
操作日志模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class Log(BaseModel):
    """操作日志模型"""
    __tablename__ = 't_log'

    user_id = db.Column(db.BigInteger, comment='操作用户ID')
    username = db.Column(db.String(50), comment='操作用户名')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    module = db.Column(db.String(50), comment='操作模块')
    description = db.Column(db.Text, comment='操作描述')
    ip = db.Column(db.String(50), comment='IP地址')
    user_agent = db.Column(db.String(500), comment='用户代理')

    @staticmethod
    def add_log(user_id, username, action, module, description, ip=None, user_agent=None):
        """添加日志"""
        log = Log(
            user_id=user_id,
            username=username,
            action=action,
            module=module,
            description=description,
            ip=ip,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()
        return log

    @staticmethod
    def get_user_logs(user_id, limit=100):
        """获取用户日志"""
        return Log.query.filter(
            Log.user_id == user_id,
            Log.status == 1
        ).order_by(Log.create_time.desc()).limit(limit).all()

    def __repr__(self):
        return f'<Log {self.action} - {self.username}>'
