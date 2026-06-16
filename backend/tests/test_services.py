"""
生产线监控系统 - 服务层单元测试
测试业务逻辑服务
"""
import pytest
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def app_context():
    """创建Flask应用上下文"""
    from flask import Flask
    from database.db import db
    import models.user
    import models.production
    import models.log
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestAuthService:
    """认证服务测试"""

    @patch('models.log.db.session')
    @patch('models.log.Log.add_log')
    @patch('services.auth_service.User')
    @patch('services.auth_service.PasswordHelper')
    @patch('services.auth_service.JWTHelper')
    def test_login_success(self, mock_jwt, mock_pwd, mock_user, mock_log_add_log, mock_db_session, app_context):
        """测试登录成功"""
        from services.auth_service import AuthService

        # Mock数据
        mock_user_obj = Mock()
        mock_user_obj.id = 1
        mock_user_obj.username = 'admin'
        mock_user_obj.password = 'hashed_password'
        mock_user_obj.role = 'admin'
        mock_user_obj.email = 'admin@example.com'
        mock_user_obj.status = 1
        mock_user_obj.create_time = datetime.now()

        mock_user.get_by_username.return_value = mock_user_obj
        mock_pwd.verify_password.return_value = True
        mock_jwt.generate_token.return_value = 'test_token'
        # Mock Log.add_log to do nothing
        mock_log_add_log.return_value = None
        # Mock db.session.add and db.session.commit to do nothing
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        response = AuthService.login('admin', 'admin123')

        assert response[1] == 200  # status_code
        data = json.loads(response[0].data)
        assert data['code'] == 200
        assert 'token' in data['data']

    @patch('services.auth_service.User')
    def test_login_user_not_found(self, mock_user, app_context):
        """测试用户不存在"""
        from services.auth_service import AuthService

        mock_user.get_by_username.return_value = None

        response = AuthService.login('nonexistent', 'password')

        assert response[1] == 404
        data = json.loads(response[0].data)
        assert data['code'] == 404

    @patch('services.auth_service.User')
    def test_login_wrong_password(self, mock_user, app_context):
        """测试密码错误"""
        from services.auth_service import AuthService
        from utils.password_helper import PasswordHelper

        mock_user_obj = Mock()
        mock_user_obj.password = 'hashed_password'
        mock_user_obj.status = 1
        mock_user.get_by_username.return_value = mock_user_obj

        with patch.object(PasswordHelper, 'verify_password', return_value=False):
            response = AuthService.login('admin', 'wrong_password')

        assert response[1] == 401

    @patch('services.auth_service.User')
    def test_login_disabled_user(self, mock_user, app_context):
        """测试禁用账号登录"""
        from services.auth_service import AuthService

        mock_user_obj = Mock()
        mock_user_obj.status = 0  # 禁用状态
        mock_user.get_by_username.return_value = mock_user_obj

        response = AuthService.login('disabled_user', 'password')

        assert response[1] == 403

    @patch('services.auth_service.User')
    def test_register_success(self, mock_user, app_context):
        """测试注册成功"""
        from services.auth_service import AuthService

        mock_user.get_by_username.return_value = None
        mock_user.get_by_email.return_value = None

        with patch('services.auth_service.PasswordHelper.hash_password', return_value='hashed'):
            response = AuthService.register('newuser', 'password123', 'new@example.com')

        assert response[1] == 201

    @patch('services.auth_service.User')
    def test_register_duplicate_username(self, mock_user, app_context):
        """测试重复用户名"""
        from services.auth_service import AuthService

        mock_user.get_by_username.return_value = Mock()  # 用户已存在

        response = AuthService.register('existing', 'password123')

        assert response[1] == 409


class TestProductionService:
    """生产线服务测试"""

    @patch('services.production_service.ProductionLine')
    @patch('services.production_service.db')
    def test_get_lines(self, mock_db, mock_line_model, app_context):
        """测试获取生产线列表"""
        from services.production_service import ProductionService

        # Mock分页结果
        mock_pagination = Mock()
        mock_line1 = Mock()
        mock_line1.id = 1
        mock_line1.line_name = '线A'
        mock_line1.status = 'running'
        mock_line1.equipments = Mock(count=Mock(return_value=2), filter_by=Mock(return_value=Mock(count=Mock(return_value=1))))
        mock_line1.to_dict = lambda: {'id': 1, 'line_name': '线A', 'status': 'running'}
        
        mock_line2 = Mock()
        mock_line2.id = 2
        mock_line2.line_name = '线B'
        mock_line2.status = 'stopped'
        mock_line2.equipments = Mock(count=Mock(return_value=3), filter_by=Mock(return_value=Mock(count=Mock(return_value=0))))
        mock_line2.to_dict = lambda: {'id': 2, 'line_name': '线B', 'status': 'stopped'}
        
        mock_pagination.items = [mock_line1, mock_line2]
        mock_pagination.total = 2
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.paginate.return_value = mock_pagination
        mock_line_model.query = mock_query

        response = ProductionService.get_lines(page=1, size=10)

        assert response[1] == 200

    @patch('services.production_service.ProductionLine')
    @patch('services.production_service.db')
    @patch('services.production_service.Log')
    def test_create_line_success(self, mock_log, mock_db, mock_line_model, app_context):
        """测试创建生产线成功"""
        from services.production_service import ProductionService

        mock_line_model.query.filter_by.return_value.first.return_value = None

        data = {
            'line_code': 'LINE-001',
            'line_name': '新生产线',
            'location': '车间A',
            'capacity': 1000
        }

        with patch('flask.g') as mock_g:
            mock_g.user_id = 1
            mock_g.username = 'admin'
            response = ProductionService.create_line(data)

        assert response[1] == 201

    @patch('services.production_service.ProductionLine')
    def test_create_line_duplicate_code(self, mock_line_model, app_context):
        """测试重复生产线编号"""
        from services.production_service import ProductionService

        mock_line_model.query.filter_by.return_value.first.return_value = Mock()

        data = {'line_code': 'LINE-001', 'line_name': '生产线'}
        response = ProductionService.create_line(data)

        assert response[1] == 409

    @patch('services.production_service.ProductionLine')
    @patch('services.production_service.Log')
    def test_update_line_success(self, mock_log, mock_line_model, app_context):
        """测试更新生产线成功"""
        from services.production_service import ProductionService

        mock_line = Mock()
        mock_line.to_dict.return_value = {'id': 1, 'line_name': '更新后的线'}
        mock_line_model.get_by_id.return_value = mock_line

        with patch('flask.g') as mock_g:
            mock_g.user_id = 1
            mock_g.username = 'admin'
            data = {'line_name': '更新后的名称', 'location': '新车间'}
            response = ProductionService.update_line(1, data)

        assert response[1] == 200

    @patch('services.production_service.ProductionLine')
    @patch('services.production_service.Log')
    def test_delete_line_success(self, mock_log, mock_line_model, app_context):
        """测试删除生产线成功"""
        from services.production_service import ProductionService

        mock_line = Mock()
        mock_line.line_name = '生产线A'
        mock_line_model.get_by_id.return_value = mock_line

        with patch('flask.g') as mock_g:
            mock_g.user_id = 1
            mock_g.username = 'admin'
            response = ProductionService.delete_line(1)

        assert response[1] == 200


class TestEquipmentService:
    """设备服务测试"""

    @patch('services.production_service.Equipment')
    @patch('services.production_service.db')
    def test_get_equipments(self, mock_db, mock_equipment, app_context):
        """测试获取设备列表"""
        from services.production_service import EquipmentService

        mock_pagination = Mock()
        mock_eq1 = Mock()
        mock_eq1.id = 1
        mock_eq1.equipment_name = '设备1'
        mock_eq1.status = 'running'
        mock_eq1.to_dict.return_value = {'id': 1}
        
        mock_eq2 = Mock()
        mock_eq2.id = 2
        mock_eq2.equipment_name = '设备2'
        mock_eq2.status = 'idle'
        mock_eq2.to_dict.return_value = {'id': 2}
        
        mock_pagination.items = [mock_eq1, mock_eq2]
        mock_pagination.total = 2
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.paginate.return_value = mock_pagination
        mock_equipment.query = mock_query

        response = EquipmentService.get_equipments(page=1, size=10)

        assert response[1] == 200

    @patch('services.production_service.Equipment')
    def test_get_equipment_by_id(self, mock_equipment, app_context):
        """测试获取设备详情"""
        from services.production_service import EquipmentService

        mock_eq = Mock()
        mock_eq.to_dict.return_value = {'id': 1, 'equipment_name': '设备1'}
        mock_eq.sensors = Mock(all=Mock(return_value=[]))
        mock_equipment.get_by_id.return_value = mock_eq

        response = EquipmentService.get_equipment_by_id(1)

        assert response[1] == 200

    @patch('services.production_service.Equipment')
    @patch('services.production_service.db')
    def test_control_equipment_start(self, mock_db, mock_equipment, app_context):
        """测试启动设备"""
        from services.production_service import EquipmentService

        mock_eq = Mock()
        mock_eq.status = 'idle'
        mock_eq.equipment_name = '设备1'
        mock_equipment.get_by_id.return_value = mock_eq

        with patch('flask.g') as mock_g:
            mock_g.user_id = 1
            mock_g.username = 'admin'
            response = EquipmentService.control_equipment(1, 'start')

        assert response[1] == 200
        assert mock_eq.status == 'running'

    @patch('services.production_service.Equipment')
    def test_control_equipment_stop(self, mock_equipment, app_context):
        """测试停止设备"""
        from services.production_service import EquipmentService

        mock_eq = Mock()
        mock_eq.status = 'running'
        mock_eq.equipment_name = '设备1'
        mock_equipment.get_by_id.return_value = mock_eq

        with patch('flask.g') as mock_g:
            mock_g.user_id = 1
            mock_g.username = 'admin'
            response = EquipmentService.control_equipment(1, 'stop')

        assert response[1] == 200
        assert mock_eq.status == 'idle'


class TestSensorService:
    """传感器服务测试"""

    @patch('services.production_service.Sensor')
    def test_get_sensors(self, mock_sensor, app_context):
        """测试获取传感器列表"""
        from services.production_service import SensorService

        mock_sensor1 = Mock()
        mock_sensor1.id = 1
        mock_sensor1.sensor_name = '传感器1'
        mock_sensor1.status = 'normal'
        mock_sensor1.to_dict.return_value = {'id': 1}
        
        mock_sensor2 = Mock()
        mock_sensor2.id = 2
        mock_sensor2.sensor_name = '传感器2'
        mock_sensor2.status = 'warning'
        mock_sensor2.to_dict.return_value = {'id': 2}
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_sensor1, mock_sensor2]
        mock_sensor.query = mock_query

        response = SensorService.get_sensors()

        assert response[1] == 200

    @patch('services.production_service.Sensor')
    def test_get_sensor_realtime_data(self, mock_sensor, app_context):
        """测试获取传感器实时数据"""
        from services.production_service import SensorService

        mock_sensor_obj = Mock()
        mock_sensor_obj.id = 1
        mock_sensor_obj.sensor_name = '温度传感器'
        mock_sensor_obj.sensor_type = 'temperature'
        mock_sensor_obj.unit = '°C'
        mock_sensor_obj.last_value = 65.5
        mock_sensor_obj.status = 'normal'
        mock_sensor_obj.equipment_id = 1
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_sensor_obj]
        mock_sensor.query = mock_query

        response = SensorService.get_sensor_realtime_data()

        assert response[1] == 200
        data = json.loads(response[0].data)
        assert 'data' in data


class TestTaskService:
    """任务服务测试"""

    @patch('services.production_service.ProductionTask')
    @patch('services.production_service.db')
    def test_create_task_success(self, mock_db, mock_task, app_context):
        """测试创建任务成功"""
        from services.production_service import TaskService

        mock_task.query.filter_by.return_value.first.return_value = None

        data = {
            'task_code': 'TASK-001',
            'task_name': '新任务',
            'quantity': 100
        }

        response = TaskService.create_task(data)

        assert response[1] == 201

    @patch('services.production_service.ProductionTask')
    def test_update_task_status(self, mock_task, app_context):
        """测试更新任务状态"""
        from services.production_service import TaskService

        mock_task_obj = Mock()
        mock_task_obj.status = 'pending'
        mock_task.get_by_id.return_value = mock_task_obj

        response = TaskService.update_task_status(1, 'in_progress')

        assert response[1] == 200
        assert mock_task_obj.status == 'in_progress'

    @patch('services.production_service.ProductionTask')
    def test_get_tasks(self, mock_task, app_context):
        """测试获取任务列表"""
        from services.production_service import TaskService

        mock_pagination = Mock()
        mock_task1 = Mock()
        mock_task1.id = 1
        mock_task1.to_dict.return_value = {'id': 1}
        
        mock_task2 = Mock()
        mock_task2.id = 2
        mock_task2.to_dict.return_value = {'id': 2}
        
        mock_pagination.items = [mock_task1, mock_task2]
        mock_pagination.total = 2
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.paginate.return_value = mock_pagination
        mock_task.query = mock_query

        response = TaskService.get_tasks(page=1, size=10)

        assert response[1] == 200


class TestStatisticsService:
    """统计服务测试"""

    @patch('services.production_service.ProductionLine')
    @patch('services.production_service.Equipment')
    @patch('services.production_service.Sensor')
    @patch('services.production_service.ProductionTask')
    @patch('services.production_service.AlertRecord')
    @patch('services.production_service.ProductionRecord')
    @patch('services.production_service.db')
    def test_get_dashboard_data(self, mock_db, mock_record, mock_alert, mock_task, mock_sensor, mock_equipment, mock_line, app_context):
        """测试获取仪表盘数据"""
        from services.production_service import StatisticsService

        # Mock统计数据
        mock_line.query.filter.return_value.count.return_value = 5
        mock_line.query.filter_by.return_value.count.return_value = 3
        mock_equipment.query.filter.return_value.count.return_value = 10
        mock_sensor.query.filter.return_value.count.return_value = 20
        mock_task.query.filter.return_value.count.return_value = 8
        mock_alert.query.filter_by.return_value.count.return_value = 2
        mock_record.query.filter.return_value.all.return_value = []

        response = StatisticsService.get_dashboard_data()

        assert response[1] == 200
        data = json.loads(response[0].data)
        assert 'production' in data['data']
        assert 'sensors' in data['data']
        assert 'tasks' in data['data']
        assert 'alerts' in data['data']

    @patch('services.production_service.ProductionRecord')
    def test_get_equipment_trend(self, mock_record, app_context):
        """测试获取设备运行趋势"""
        from services.production_service import StatisticsService

        mock_record.query.filter.return_value.order_by.return_value.all.return_value = []

        response = StatisticsService.get_equipment_trend(days=7)

        assert response[1] == 200
        data = json.loads(response[0].data)
        assert 'labels' in data['data']
        assert 'values' in data['data']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
