"""
生产线监控系统 - 单元测试
测试后端服务和工具函数
"""
import pytest
import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config


class TestConfig:
    """配置类测试"""
    
    def test_config_secret_key(self):
        """测试SECRET_KEY存在"""
        from config import DevelopmentConfig
        assert DevelopmentConfig.SECRET_KEY is not None
    
    def test_config_debug_mode(self):
        """测试调试模式"""
        from config import DevelopmentConfig, ProductionConfig, TestingConfig
        assert DevelopmentConfig.DEBUG is True
        assert ProductionConfig.DEBUG is False
        assert TestingConfig.DEBUG is True
    
    def test_config_database_uri(self):
        """测试数据库URI配置"""
        from config import Config
        config = Config()
        assert hasattr(config, 'DATABASE_URI')
        assert config.DATABASE_URI is not None
    
    def test_config_jwt_settings(self):
        """测试JWT配置"""
        from config import Config
        assert hasattr(Config, 'JWT_SECRET_KEY')
        assert hasattr(Config, 'JWT_ALGORITHM')
        assert hasattr(Config, 'JWT_EXPIRE_HOURS')
        assert Config.JWT_ALGORITHM == 'HS256'
    
    def test_config_by_name(self):
        """测试配置字典"""
        from config import config_by_name
        assert 'development' in config_by_name
        assert 'production' in config_by_name
        assert 'testing' in config_by_name


class TestPasswordHelper:
    """密码工具测试"""
    
    def test_password_hash_and_verify(self):
        """测试密码加密和验证"""
        from utils.password_helper import PasswordHelper
        
        password = "test123"
        hashed = PasswordHelper.hash_password(password)
        
        assert hashed != password
        assert PasswordHelper.verify_password(password, hashed)
        assert not PasswordHelper.verify_password("wrong_password", hashed)
    
    def test_validate_password_strength(self):
        """测试密码强度验证"""
        from utils.password_helper import PasswordHelper
        
        # 弱密码
        result = PasswordHelper.validate_password_strength("123")
        assert result['valid'] is False
        
        # 强密码
        result = PasswordHelper.validate_password_strength("test123")
        assert result['valid'] is True


class TestResponseFormatter:
    """响应格式化工具测试"""
    
    @pytest.fixture
    def app_context(self):
        """创建Flask应用上下文"""
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            yield app
    
    def test_success_response(self, app_context):
        """测试成功响应格式化"""
        from utils.response import Response
        import json
        
        result, status_code = Response.success({"id": 1}, "操作成功")
        assert status_code == 200
        data = json.loads(result.data)
        assert data['code'] == 200
        assert data['message'] == "操作成功"
    
    def test_error_response(self, app_context):
        """测试错误响应格式化"""
        from utils.response import Response
        import json
        
        result, status_code = Response.error("操作失败", 400)
        assert status_code == 400
        data = json.loads(result.data)
        assert data['code'] == 400
        assert data['message'] == "操作失败"
    
    def test_paginate_response(self, app_context):
        """测试分页响应格式化"""
        from utils.response import Response
        import json
        
        items = [{"id": 1}, {"id": 2}]
        result, status_code = Response.paginate(items, 10, 1, 10)
        
        assert status_code == 200
        data = json.loads(result.data)
        assert data['data']['total'] == 10
        assert data['data']['page'] == 1
        assert len(data['data']['items']) == 2


class TestJWTHelper:
    """JWT工具测试"""
    
    def test_generate_and_decode_token(self):
        """测试JWT Token生成和解析"""
        from utils.jwt_helper import JWTHelper
        
        token = JWTHelper.generate_token(1, "admin", "admin")
        assert token is not None
        
        result = JWTHelper.decode_token(token)
        assert result['valid'] is True
        assert result['data']['user_id'] == 1
        assert result['data']['username'] == "admin"
    
    def test_invalid_token(self):
        """测试无效Token"""
        from utils.jwt_helper import JWTHelper
        
        result = JWTHelper.decode_token("invalid_token")
        assert result['valid'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
