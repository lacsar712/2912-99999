"""
测试配置文件
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


@pytest.fixture(scope='session')
def test_config():
    """测试配置"""
    return {
        'TESTING': True,
        'DEBUG': True,
        'SECRET_KEY': 'test-secret-key',
        'DATABASE': {
            'mysql': {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '123456',
                'database': 'test_db'
            }
        }
    }


@pytest.fixture(scope='function')
def app(test_config):
    """创建测试应用"""
    from app import create_app
    app = create_app()
    app.config.update(test_config)
    return app
