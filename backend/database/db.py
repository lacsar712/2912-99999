"""
数据库连接模块
"""
import time
import logging
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def init_db(app, max_retries=30, retry_interval=2):
    """
    初始化数据库，带有重试机制
    
    Args:
        app: Flask应用实例
        max_retries: 最大重试次数
        retry_interval: 重试间隔(秒)
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = Config().DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = Config.DEBUG if hasattr(Config, 'DEBUG') else False

    db.init_app(app)

    # 带重试机制的数据库连接
    with app.app_context():
        for attempt in range(max_retries):
            try:
                db.create_all()
                logger.info("Database initialized successfully")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    time.sleep(retry_interval)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
