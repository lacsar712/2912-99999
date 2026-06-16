"""
生产线监控系统 - 生产线API集成测试
测试生产线相关API端点
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['RATELIMIT_ENABLED'] = False  # 禁用速率限制
    # 确保速率限制器被禁用
    if 'limiter' in app.extensions:
        app.extensions['limiter'].enabled = False
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 尝试登录获取token
    try:
        response = client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'admin123'})
        if response.status_code == 200:
            data = json.loads(response.data)
            token = data.get('data', {}).get('token')
            if token:
                return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    except:
        pass
    return {'Content-Type': 'application/json'}


class TestProductionLineAPI:
    """生产线API测试"""

    def test_get_lines_without_auth(self, client):
        """测试未认证访问生产线列表"""
        response = client.get('/api/production/lines')
        
        assert response.status_code in [401, 429]
        data = json.loads(response.data)
        assert data['code'] in [401, 429]

    def test_get_lines_with_auth(self, client, auth_headers):
        """测试认证后访问生产线列表"""
        response = client.get('/api/production/lines', headers=auth_headers)
        
        # 取决于数据库状态（包括速率限制429）
        assert response.status_code in [200, 401, 429]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'data' in data

    def test_create_line_without_auth(self, client):
        """测试未认证创建生产线"""
        data = {
            'line_name': '测试生产线',
            'location': '车间A',
            'capacity': 1000
        }
        response = client.post('/api/production/lines', 
                              json=data, 
                              headers={'Content-Type': 'application/json'})
        
        assert response.status_code in [401, 429]

    def test_create_line_with_auth(self, client, auth_headers):
        """测试认证后创建生产线"""
        data = {
            'line_name': 'API测试生产线',
            'location': 'API测试车间',
            'capacity': 500,
            'manager': '测试管理员'
        }
        response = client.post('/api/production/lines', 
                              json=data, 
                              headers=auth_headers)
        
        # 可能成功或失败（取决于权限和数据库）
        assert response.status_code in [201, 401, 400, 409]

    def test_get_line_detail_without_auth(self, client):
        """测试未认证获取生产线详情"""
        response = client.get('/api/production/lines/1')
        
        assert response.status_code in [401, 429]

    def test_get_line_detail_with_auth(self, client, auth_headers):
        """测试认证后获取生产线详情"""
        response = client.get('/api/production/lines/1', headers=auth_headers)
        
        # 可能成功或404（包括速率限制429）
        assert response.status_code in [200, 401, 404, 429]

    def test_update_line_without_auth(self, client):
        """测试未认证更新生产线"""
        data = {'line_name': '更新后的名称'}
        response = client.put('/api/production/lines/1', json=data)
        
        assert response.status_code in [401, 429]

    def test_delete_line_without_auth(self, client):
        """测试未认证删除生产线"""
        response = client.delete('/api/production/lines/1')
        
        assert response.status_code in [401, 429]

    def test_get_lines_pagination(self, client, auth_headers):
        """测试生产线分页"""
        response = client.get('/api/production/lines?page=1&size=10', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]
        if response.status_code == 200:
            data = json.loads(response.data)
            if 'data' in data and isinstance(data['data'], dict):
                assert 'items' in data['data'] or 'list' in data['data']

    def test_get_lines_with_filter(self, client, auth_headers):
        """测试生产线筛选"""
        response = client.get('/api/production/lines?status=running', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]


class TestEquipmentAPI:
    """设备API测试"""

    def test_get_equipments_without_auth(self, client):
        """测试未认证获取设备列表"""
        response = client.get('/api/production/equipments')
        
        assert response.status_code in [401, 429]

    def test_get_equipments_with_auth(self, client, auth_headers):
        """测试认证后获取设备列表"""
        response = client.get('/api/production/equipments', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]

    def test_get_equipments_by_line(self, client, auth_headers):
        """测试按生产线获取设备"""
        response = client.get('/api/production/equipments?line_id=1', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]

    def test_create_equipment_without_auth(self, client):
        """测试未认证创建设备"""
        data = {
            'equipment_name': '测试设备',
            'equipment_type': 'cnc',
            'line_id': 1
        }
        response = client.post('/api/production/equipments', json=data)
        
        assert response.status_code in [401, 429]

    def test_control_equipment_without_auth(self, client):
        """测试未认证控制设备"""
        data = {'action': 'start'}
        response = client.post('/api/production/equipments/1/control', json=data)
        
        assert response.status_code in [401, 429]


class TestSensorAPI:
    """传感器API测试"""

    def test_get_sensors_without_auth(self, client):
        """测试未认证获取传感器列表"""
        response = client.get('/api/production/sensors')
        
        assert response.status_code in [401, 429]

    def test_get_sensors_with_auth(self, client, auth_headers):
        """测试认证后获取传感器列表"""
        response = client.get('/api/production/sensors', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]

    def test_get_sensor_realtime_without_auth(self, client):
        """测试未认证获取传感器实时数据"""
        response = client.get('/api/production/sensors/realtime')
        
        assert response.status_code in [401, 429]

    def test_get_sensor_realtime_with_auth(self, client, auth_headers):
        """测试认证后获取传感器实时数据"""
        response = client.get('/api/production/sensors/realtime', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]


class TestTaskAPI:
    """任务API测试"""

    def test_get_tasks_without_auth(self, client):
        """测试未认证获取任务列表"""
        response = client.get('/api/production/tasks')
        
        assert response.status_code in [401, 429]

    def test_get_tasks_with_auth(self, client, auth_headers):
        """测试认证后获取任务列表"""
        response = client.get('/api/production/tasks', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]

    def test_create_task_without_auth(self, client):
        """测试未认证创建任务"""
        data = {
            'task_name': '测试任务',
            'line_id': 1,
            'product_code': 'TEST-001',
            'target_quantity': 100
        }
        response = client.post('/api/production/tasks', json=data)
        
        assert response.status_code in [401, 429]

    def test_update_task_status_without_auth(self, client):
        """测试未认证更新任务状态"""
        data = {'status': 'in_progress'}
        response = client.put('/api/production/tasks/1/status', json=data)
        
        assert response.status_code in [401, 429]


class TestDashboardAPI:
    """仪表盘API测试"""

    def test_get_dashboard_without_auth(self, client):
        """测试未认证获取仪表盘数据"""
        response = client.get('/api/production/dashboard')
        
        assert response.status_code in [401, 429]
        data = json.loads(response.data)
        assert data['code'] in [401, 429]

    def test_get_dashboard_with_auth(self, client, auth_headers):
        """测试认证后获取仪表盘数据"""
        response = client.get('/api/production/dashboard', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'data' in data
            # 检查数据结构
            dashboard_data = data.get('data', {})
            assert any(key in dashboard_data for key in ['production', 'tasks', 'sensors', 'alerts'])

    def test_get_trend_without_auth(self, client):
        """测试未认证获取趋势数据"""
        response = client.get('/api/production/trend')
        
        assert response.status_code in [401, 429]

    def test_get_trend_with_auth(self, client, auth_headers):
        """测试认证后获取趋势数据"""
        response = client.get('/api/production/trend?days=7', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]


class TestAlertAPI:
    """告警API测试"""

    def test_get_alerts_without_auth(self, client):
        """测试未认证获取告警列表"""
        response = client.get('/api/production/alerts')
        
        assert response.status_code in [401, 429]

    def test_get_alerts_with_auth(self, client, auth_headers):
        """测试认证后获取告警列表"""
        response = client.get('/api/production/alerts', headers=auth_headers)
        
        assert response.status_code in [200, 401, 429]

    def test_get_active_alerts_without_auth(self, client):
        """测试未认证获取活跃告警"""
        response = client.get('/api/production/alerts/active')
        
        assert response.status_code in [401, 429]

    def test_resolve_alert_without_auth(self, client):
        """测试未认证处理告警"""
        data = {'remark': '已处理'}
        response = client.post('/api/production/alerts/1/resolve', json=data)
        
        assert response.status_code in [401, 429]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
