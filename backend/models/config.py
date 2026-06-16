"""
系统配置模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class Config(BaseModel):
    """系统配置模型"""
    __tablename__ = 't_config'

    config_key = db.Column(db.String(100), unique=True, nullable=False, comment='配置键')
    config_value = db.Column(db.Text, comment='配置值')
    config_type = db.Column(db.String(20), default='string', comment='配置类型')
    description = db.Column(db.String(200), comment='配置描述')

    @staticmethod
    def get_value(key, default=None):
        """获取配置值"""
        config = Config.query.filter(
            Config.config_key == key,
            Config.status == 1
        ).first()

        if config:
            return config.config_value
        return default

    @staticmethod
    def set_value(key, value, config_type='string', description=None):
        """设置配置值"""
        config = Config.query.filter(Config.config_key == key).first()

        if config:
            config.config_value = value
            config.config_type = config_type
            if description:
                config.description = description
        else:
            config = Config(
                config_key=key,
                config_value=value,
                config_type=config_type,
                description=description
            )
            db.session.add(config)

        db.session.commit()
        return config

    def __repr__(self):
        return f'<Config {self.config_key}>'
