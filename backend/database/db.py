"""
数据库连接模块
"""
import time
import logging
from sqlalchemy import inspect, text
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
logger = logging.getLogger(__name__)

# 增量 schema 迁移：为已存在的数据库补充缺失列
SCHEMA_MIGRATIONS = [
    {
        'table': 't_user',
        'column': 'position',
        'sql': "ALTER TABLE t_user ADD COLUMN position VARCHAR(100) COMMENT '岗位'",
    },
]


def _apply_schema_migrations():
    """为已有表补充模型新增但数据库缺失的列"""
    inspector = inspect(db.engine)
    for migration in SCHEMA_MIGRATIONS:
        table = migration['table']
        column = migration['column']
        if table not in inspector.get_table_names():
            continue
        existing = {col['name'] for col in inspector.get_columns(table)}
        if column in existing:
            continue
        db.session.execute(text(migration['sql']))
        db.session.commit()
        logger.info(f"Schema migration: added column {table}.{column}")


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

    # 确保所有模型已注册后再建表
    import models  # noqa: F401

    # 带重试机制的数据库连接
    with app.app_context():
        for attempt in range(max_retries):
            try:
                db.create_all()
                _apply_schema_migrations()
                logger.info("Database initialized successfully")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    time.sleep(retry_interval)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
