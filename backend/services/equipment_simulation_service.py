"""
设备管理页面数据模拟服务
专门为设备管理页面生成模拟数据
支持多数据源、分页、定时刷新等功能
"""
import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from flask import g
from database.db import db
from models.production import Equipment, ProductionLine, Sensor
from models.log import Log
from utils.response import Response


class EquipmentSimulationService:
    """设备管理页面数据模拟服务类"""
    
    # 设备状态分布
    EQUIPMENT_STATUSES = ['running', 'idle', 'maintenance', 'error', 'offline']
    STATUS_WEIGHTS = [0.5, 0.3, 0.1, 0.05, 0.05]  # 运行:50%, 空闲:30%, 维护:10%, 错误:5%, 离线:5%
    
    # 设备类型
    EQUIPMENT_TYPES = [
        '注塑机', '冲压机', '焊接机器人', '装配线', '包装机',
        '检测设备', '输送带', '切割机', '喷涂设备', '烘干炉'
    ]
    
    # 制造商
    MANUFACTURERS = ['厂商A', '厂商B', '厂商C', '厂商D', '厂商E']
    
    # 设备型号前缀
    MODEL_PREFIXES = ['MODEL-', 'TYPE-', 'VERSION-', 'GEN-']
    
    # 传感器类型
    SENSOR_TYPES = ['temperature', 'pressure', 'humidity', 'speed', 'vibration', 'current', 'voltage']
    
    # 位置
    LOCATIONS = ['A车间', 'B车间', 'C车间', 'D车间', 'E车间', '中央仓库', '测试区']
    
    @staticmethod
    def generate_equipment_simulation_data(
        page: int = 1,
        size: int = 10,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        use_real_data: bool = False
    ) -> Tuple[Dict, int]:
        """
        生成设备模拟数据
        
        Args:
            page: 页码
            size: 每页大小
            line_id: 生产线ID筛选
            status: 设备状态筛选
            source_ids: 数据源ID列表（如果提供，则从指定数据源获取数据）
            use_real_data: 是否使用真实数据库中的数据（如果数据库中有数据）
            
        Returns:
            (data_dict, total_count): 数据字典和总数量
        """
        # 如果使用真实数据且数据库中有数据，则返回真实数据
        if use_real_data:
            return EquipmentSimulationService._get_real_equipment_data(page, size, line_id, status)
        
        # 否则生成模拟数据
        return EquipmentSimulationService._generate_mock_equipment_data(page, size, line_id, status, source_ids)
    
    @staticmethod
    def _get_real_equipment_data(
        page: int,
        size: int,
        line_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Tuple[Dict, int]:
        """获取真实数据库中的设备数据"""
        from services.production_service import EquipmentService
        # 这里直接调用现有的EquipmentService获取数据
        # 但为了保持接口一致性，我们重新实现查询逻辑
        query = Equipment.query.filter(Equipment.status != 0)
        
        if line_id:
            query = query.filter(Equipment.line_id == line_id)
        if status:
            query = query.filter(Equipment.status == status)
        
        total = query.count()
        pagination = query.order_by(Equipment.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        items = []
        for equipment in pagination.items:
            item = equipment.to_dict()
            # 添加传感器数量信息
            item['sensor_count'] = equipment.sensors.count()
            item['running_sensor_count'] = equipment.sensors.filter_by(status='normal').count()
            item['warning_sensor_count'] = equipment.sensors.filter_by(status='warning').count()
            items.append(item)
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size if size > 0 else 0
        }, total
    
    @staticmethod
    def _generate_mock_equipment_data(
        page: int,
        size: int,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
        source_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, int]:
        """生成模拟设备数据"""
        
        # 如果有指定的数据源，从数据源获取数据
        if source_ids:
            return EquipmentSimulationService._get_data_from_sources(source_ids, page, size)
        
        # 否则生成纯模拟数据
        total = random.randint(50, 200)  # 模拟总数据量
        start_idx = (page - 1) * size
        end_idx = min(start_idx + size, total)
        
        items = []
        for i in range(start_idx, end_idx):
            # 生成设备状态（如果未指定状态则随机生成）
            equipment_status = status if status else random.choices(
                EquipmentSimulationService.EQUIPMENT_STATUSES,
                weights=EquipmentSimulationService.STATUS_WEIGHTS
            )[0]
            
            # 根据状态生成相关数据
            if equipment_status == 'running':
                runtime_hours = random.uniform(100, 10000)
                temperature = random.uniform(25, 75)
                pressure = random.uniform(20, 80)
                speed = random.uniform(500, 2500)
                sensor_count = random.randint(3, 8)
                running_sensor_count = sensor_count - random.randint(0, 2)
                warning_sensor_count = random.randint(0, 2)
            elif equipment_status == 'idle':
                runtime_hours = random.uniform(100, 5000)
                temperature = random.uniform(20, 30)
                pressure = random.uniform(0, 10)
                speed = 0
                sensor_count = random.randint(2, 6)
                running_sensor_count = sensor_count
                warning_sensor_count = 0
            elif equipment_status == 'maintenance':
                runtime_hours = random.uniform(500, 8000)
                temperature = random.uniform(20, 40)
                pressure = random.uniform(0, 20)
                speed = 0
                sensor_count = random.randint(2, 5)
                running_sensor_count = 0
                warning_sensor_count = sensor_count
            elif equipment_status == 'error':
                runtime_hours = random.uniform(1000, 5000)
                temperature = random.uniform(60, 90)
                pressure = random.uniform(70, 100)
                speed = random.uniform(0, 100)
                sensor_count = random.randint(1, 4)
                running_sensor_count = 0
                warning_sensor_count = sensor_count
            else:  # offline
                runtime_hours = random.uniform(0, 3000)
                temperature = random.uniform(15, 25)
                pressure = random.uniform(0, 5)
                speed = 0
                sensor_count = random.randint(0, 3)
                running_sensor_count = 0
                warning_sensor_count = 0
            
            # 生产线ID（如果未指定则随机生成）
            equipment_line_id = line_id if line_id else random.randint(1, 5)
            
            # 生成设备数据
            equipment_data = {
                'id': i + 1,
                'equipment_code': f'EQP-{1000 + i}',
                'equipment_name': f'{random.choice(EquipmentSimulationService.EQUIPMENT_TYPES)}-{i+1}',
                'equipment_type': random.choice(EquipmentSimulationService.EQUIPMENT_TYPES),
                'line_id': equipment_line_id,
                'line_name': f'生产线{equipment_line_id}',
                'status': equipment_status,
                'model': f'{random.choice(EquipmentSimulationService.MODEL_PREFIXES)}{random.randint(100, 999)}',
                'manufacturer': random.choice(EquipmentSimulationService.MANUFACTURERS),
                'purchase_date': (datetime.now() - timedelta(days=random.randint(100, 1000))).strftime('%Y-%m-%d'),
                'install_date': (datetime.now() - timedelta(days=random.randint(50, 500))).strftime('%Y-%m-%d'),
                'runtime_hours': round(runtime_hours, 2),
                'temperature': round(temperature, 2),
                'pressure': round(pressure, 2),
                'speed': round(speed, 2),
                'sensor_count': sensor_count,
                'running_sensor_count': running_sensor_count,
                'warning_sensor_count': warning_sensor_count,
                'location': random.choice(EquipmentSimulationService.LOCATIONS),
                'last_maintenance': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S'),
                'next_maintenance': (datetime.now() + timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d %H:%M:%S'),
                'create_time': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            items.append(equipment_data)
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size if size > 0 else 0
        }, total
    
    @staticmethod
    def _get_data_from_sources(source_ids: List[str], page: int, size: int) -> Tuple[Dict, int]:
        """从指定数据源获取设备数据（简化版，返回空数据）"""
        # 由于中心控制模块已删除，返回空数据
        return {
            'items': [],
            'total': 0,
            'page': page,
            'size': size,
            'pages': 0
        }, 0
    
    @staticmethod
    def _convert_to_equipment_format(data: List[Dict], source_id: str) -> List[Dict]:
        """将数据源数据转换为设备数据格式"""
        equipment_list = []
        
        for i, item in enumerate(data):
            # 根据数据源类型转换数据
            if source_id.startswith('api_'):
                equipment_data = EquipmentSimulationService._convert_api_data(item, i)
            elif source_id.startswith('websocket_'):
                equipment_data = EquipmentSimulationService._convert_websocket_data(item, i)
            elif source_id.startswith('file_stream_'):
                equipment_data = EquipmentSimulationService._convert_file_stream_data(item, i)
            elif source_id.startswith('user_input_'):
                equipment_data = EquipmentSimulationService._convert_user_input_data(item, i)
            else:
                # 默认转换
                equipment_data = EquipmentSimulationService._create_default_equipment_data(item, i, source_id)
            
            equipment_list.append(equipment_data)
        
        return equipment_list
    
    @staticmethod
    def _convert_api_data(api_data: Dict, index: int) -> Dict:
        """转换API数据为设备格式"""
        return {
            'id': index + 1000,  # 避免与模拟数据ID冲突
            'equipment_code': f'API-EQP-{index}',
            'equipment_name': f'API设备{index}',
            'equipment_type': 'API设备',
            'line_id': random.randint(1, 3),
            'line_name': f'生产线{random.randint(1, 3)}',
            'status': random.choice(['running', 'idle']),
            'model': 'API-MODEL',
            'manufacturer': 'API厂商',
            'runtime_hours': round(random.uniform(100, 5000), 2),
            'temperature': round(random.uniform(20, 60), 2),
            'pressure': round(random.uniform(10, 70), 2),
            'speed': round(random.uniform(0, 2000), 2),
            'sensor_count': random.randint(2, 6),
            'running_sensor_count': random.randint(2, 6),
            'warning_sensor_count': random.randint(0, 1),
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _convert_websocket_data(ws_data: Dict, index: int) -> Dict:
        """转换WebSocket数据为设备格式"""
        return {
            'id': index + 2000,
            'equipment_code': f'WS-EQP-{index}',
            'equipment_name': f'WebSocket设备{index}',
            'equipment_type': '实时设备',
            'line_id': random.randint(1, 3),
            'line_name': f'生产线{random.randint(1, 3)}',
            'status': 'running',  # WebSocket设备通常是在线的
            'model': 'WS-MODEL',
            'manufacturer': 'WS厂商',
            'runtime_hours': round(random.uniform(500, 8000), 2),
            'temperature': round(random.uniform(25, 70), 2),
            'pressure': round(random.uniform(20, 80), 2),
            'speed': round(random.uniform(500, 2500), 2),
            'sensor_count': random.randint(4, 8),
            'running_sensor_count': random.randint(3, 7),
            'warning_sensor_count': random.randint(0, 2),
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _convert_file_stream_data(file_data: Dict, index: int) -> Dict:
        """转换文件流数据为设备格式"""
        return {
            'id': index + 3000,
            'equipment_code': f'FILE-EQP-{index}',
            'equipment_name': f'文件设备{index}',
            'equipment_type': '文件设备',
            'line_id': random.randint(1, 3),
            'line_name': f'生产线{random.randint(1, 3)}',
            'status': random.choice(['running', 'idle', 'offline']),
            'model': 'FILE-MODEL',
            'manufacturer': '文件厂商',
            'runtime_hours': round(random.uniform(0, 3000), 2),
            'temperature': round(random.uniform(15, 40), 2),
            'pressure': round(random.uniform(0, 50), 2),
            'speed': round(random.uniform(0, 1000), 2),
            'sensor_count': random.randint(1, 4),
            'running_sensor_count': random.randint(0, 3),
            'warning_sensor_count': random.randint(0, 2),
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _convert_user_input_data(user_data: Dict, index: int) -> Dict:
        """转换用户输入数据为设备格式"""
        return {
            'id': index + 4000,
            'equipment_code': f'USER-EQP-{index}',
            'equipment_name': f'用户设备{index}',
            'equipment_type': '用户设备',
            'line_id': random.randint(1, 3),
            'line_name': f'生产线{random.randint(1, 3)}',
            'status': random.choice(['running', 'idle', 'maintenance']),
            'model': 'USER-MODEL',
            'manufacturer': '用户厂商',
            'runtime_hours': round(random.uniform(100, 2000), 2),
            'temperature': round(random.uniform(20, 50), 2),
            'pressure': round(random.uniform(10, 60), 2),
            'speed': round(random.uniform(0, 1500), 2),
            'sensor_count': random.randint(2, 5),
            'running_sensor_count': random.randint(1, 4),
            'warning_sensor_count': random.randint(0, 2),
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _create_default_equipment_data(data: Dict, index: int, source_id: str) -> Dict:
        """创建默认设备数据"""
        return {
            'id': index + 5000,
            'equipment_code': f'SRC-{source_id[:8]}-{index}',
            'equipment_name': f'数据源设备{index}',
            'equipment_type': '通用设备',
            'line_id': 1,
            'line_name': '生产线1',
            'status': 'running',
            'model': 'GENERIC',
            'manufacturer': '通用厂商',
            'runtime_hours': 1000.0,
            'temperature': 25.0,
            'pressure': 50.0,
            'speed': 1000.0,
            'sensor_count': 4,
            'running_sensor_count': 3,
            'warning_sensor_count': 1,
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_equipment_simulation_config() -> Dict[str, Any]:
        """获取设备模拟配置"""
        return {
            'data_sources': {
                'enabled': True,
                'max_sources': 5,
                'default_sources': ['api', 'websocket']
            },
            'pagination': {
                'default_page': 1,
                'default_size': 10,
                'max_size': 100
            },
            'refresh': {
                'auto_refresh': False,
                'refresh_interval': 30,  # 秒
                'manual_refresh': True
            },
            'data_generation': {
                'total_range': [50, 200],
                'status_distribution': dict(zip(
                    EquipmentSimulationService.EQUIPMENT_STATUSES,
                    EquipmentSimulationService.STATUS_WEIGHTS
                )),
                'sensor_range': [1, 8],
                'runtime_range': [0, 10000]
            }
        }
    
    @staticmethod
    def start_auto_refresh(interval: int = 30, callback_url: Optional[str] = None):
        """启动自动刷新（模拟实时数据更新）"""
        def refresh_task():
            while True:
                try:
                    # 模拟数据更新
                    # 这里可以调用数据源管理器获取最新数据
                    # 或者生成新的模拟数据
                    if callback_url:
                        # 如果有回调URL，可以发送HTTP请求通知数据更新
                        pass
                except Exception as e:
                    print(f"自动刷新任务错误: {e}")
                time.sleep(interval)
        
        thread = threading.Thread(target=refresh_task, daemon=True)
        thread.start()
        return thread
    
    @staticmethod
    def create_mock_equipment_data_source(
        source_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建设备模拟数据源（简化版）"""
        try:
            # 简化实现，不再依赖DataSourceManager
            import uuid
            source_id = f"{source_type}_{uuid.uuid4().hex[:8]}"
            
            # 记录操作日志
            Log.add_log(
                g.user_id if hasattr(g, 'user_id') else 0,
                g.username if hasattr(g, 'username') else 'system',
                'create',
                'equipment_simulation',
                f'创建设备模拟数据源: {source_type} ({source_id})'
            )
            
            return {
                'source_id': source_id,
                'type': source_type,
                'config': config,
                'status': 'created'
            }
            
        except Exception as e:
            return {
                'error': f'创建设备模拟数据源失败: {str(e)}',
                'status': 'error'
            }