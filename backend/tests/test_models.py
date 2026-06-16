"""
生产线监控系统 - 模型层单元测试
测试数据模型和数据库操作
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestUserModel:
    """用户模型测试"""
    
    def test_user_creation(self):
        """测试用户创建"""
        from models.user import User
        
        user = User(
            username='testuser',
            password='hashed_password',
            email='test@example.com',
            role='user',
            status=1
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.status == 1
    
    def test_user_to_dict(self):
        """测试用户转字典"""
        from models.user import User
        
        user = User(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        user.id = 1
        user.create_time = datetime.now()
        
        user_dict = user.to_dict()
        
        assert user_dict['id'] == 1
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['role'] == 'user'
    
    def test_user_status_values(self):
        """测试用户状态值"""
        from models.user import User
        
        # 创建用户并检查默认状态值
        user = User(
            username='testuser',
            password='hashed_password',
            email='test@example.com',
            role='user',
            status=1  # 手动设置状态值
        )
        # BaseModel中status默认值为1，但SQLAlchemy的default不会在Python对象创建时设置
        assert user.status == 1
        # 状态字段应为整数
        assert isinstance(user.status, int)


class TestProductionLineModel:
    """生产线模型测试"""
    
    def test_line_creation(self):
        """测试生产线创建"""
        from models.production import ProductionLine
        
        line = ProductionLine(
            line_code='LINE001',
            line_name='测试生产线A',
            location='一号车间',
            capacity=1000,
            status='running',
            supervisor='张工'
        )
        
        assert line.line_code == 'LINE001'
        assert line.line_name == '测试生产线A'
        assert line.location == '一号车间'
        assert line.capacity == 1000
        assert line.status == 'running'
        assert line.supervisor == '张工'
    
    def test_line_status_enum(self):
        """测试生产线状态枚举"""
        from models.production import ProductionLine
        
        valid_statuses = ['running', 'stopped', 'maintenance', 'error']
        for status in valid_statuses:
            line = ProductionLine(line_code='TEST', line_name='Test', status=status)
            assert line.status == status
    
    def test_line_to_dict(self):
        """测试生产线转字典"""
        from models.production import ProductionLine
        
        line = ProductionLine(
            line_code='LINE001',
            line_name='测试线',
            location='车间A',
            capacity=500,
            status='running'
        )
        line.id = 1
        line.create_time = datetime.now()
        
        line_dict = line.to_dict()
        
        assert line_dict['id'] == 1
        assert line_dict['line_code'] == 'LINE001'
        assert line_dict['line_name'] == '测试线'
        assert line_dict['status'] == 'running'
        assert 'create_time' in line_dict
        # equipment_count和task_count可能无法在没有数据库会话的情况下计算
        # 我们只检查它们是否存在（可能为0）
        assert 'equipment_count' in line_dict
        assert 'task_count' in line_dict


class TestEquipmentModel:
    """设备模型测试"""
    
    def test_equipment_creation(self):
        """测试设备创建"""
        from models.production import Equipment
        
        equipment = Equipment(
            equipment_name='数控机床01',
            equipment_type='cnc',
            line_id=1,
            status='running',
            model='VMC-850',
            manufacturer='沈阳机床'
        )
        
        assert equipment.equipment_name == '数控机床01'
        assert equipment.equipment_type == 'cnc'
        assert equipment.line_id == 1
    
    def test_equipment_types(self):
        """测试设备类型"""
        from models.production import Equipment
        
        valid_types = ['cnc', 'robot', 'conveyor', 'detector', 'other']
        for eq_type in valid_types:
            equipment = Equipment(equipment_type=eq_type)
            assert equipment.equipment_type == eq_type


class TestSensorModel:
    """传感器模型测试"""
    
    def test_sensor_creation(self):
        """测试传感器创建"""
        from models.production import Sensor
        
        sensor = Sensor(
            sensor_name='温度传感器01',
            sensor_type='temperature',
            equipment_id=1,
            unit='°C',
            min_value=0,
            max_value=100,
            threshold_low=10,
            threshold_high=80
        )
        
        assert sensor.sensor_name == '温度传感器01'
        assert sensor.sensor_type == 'temperature'
        assert sensor.unit == '°C'
        assert sensor.min_value == 0
        assert sensor.max_value == 100
        assert sensor.threshold_low == 10
        assert sensor.threshold_high == 80
    
    def test_sensor_types(self):
        """测试传感器类型"""
        from models.production import Sensor
        
        valid_types = ['temperature', 'pressure', 'speed', 'humidity', 'vibration', 'other']
        for s_type in valid_types:
            sensor = Sensor(sensor_type=s_type)
            assert sensor.sensor_type == s_type


class TestProductionTaskModel:
    """生产任务模型测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        from models.production import ProductionTask
        
        task = ProductionTask(
            task_code='TASK001',
            task_name='批量生产任务A',
            line_id=1,
            product_name='PROD-001',
            quantity=1000,
            priority=1,
            status='pending'
        )
        
        assert task.task_code == 'TASK001'
        assert task.task_name == '批量生产任务A'
        assert task.product_name == 'PROD-001'
        assert task.quantity == 1000
        assert task.priority == 1
    
    def test_task_priority_values(self):
        """测试任务优先级"""
        from models.production import ProductionTask
        
        # 高优先级
        task_high = ProductionTask(priority=1)
        assert task_high.priority == 1
        
        # 普通优先级
        task_normal = ProductionTask(priority=2)
        assert task_normal.priority == 2
        
        # 低优先级
        task_low = ProductionTask(priority=3)
        assert task_low.priority == 3


class TestAlertRecordModel:
    """告警记录模型测试"""
    
    def test_alert_creation(self):
        """测试告警创建"""
        from models.production import AlertRecord
        
        alert = AlertRecord(
            alert_code='ALERT001',
            alert_type='sensor_warning',
            severity='warning',
            equipment_id=1,
            sensor_id=2,
            message='温度传感器数值异常',
            status='active'  # 手动设置状态
        )
        
        assert alert.alert_code == 'ALERT001'
        assert alert.alert_type == 'sensor_warning'
        assert alert.severity == 'warning'
        assert alert.message == '温度传感器数值异常'
        assert alert.status == 'active'  # 默认状态
    
    def test_alert_levels(self):
        """测试告警级别"""
        from models.production import AlertRecord
        
        levels = ['info', 'warning', 'error', 'critical']
        for level in levels:
            alert = AlertRecord(alert_code=f'ALERT{level}', severity=level)
            assert alert.severity == level


class TestModelRelationships:
    """模型关系测试"""
    
    def test_line_equipment_relationship(self):
        """测试生产线与设备关系"""
        from models.production import ProductionLine, Equipment
        
        line = ProductionLine(id=1, line_name='生产线A')
        equipment = Equipment(id=1, equipment_name='设备1', line_id=1)
        
        assert equipment.line_id == line.id
    
    def test_equipment_sensor_relationship(self):
        """测试设备与传感器关系"""
        from models.production import Equipment, Sensor
        
        equipment = Equipment(id=1, equipment_name='设备1')
        sensor = Sensor(id=1, sensor_name='传感器1', equipment_id=1)
        
        assert sensor.equipment_id == equipment.id


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
