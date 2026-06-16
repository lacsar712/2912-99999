"""
数据模拟服务
支持生成模拟生产线监控数据
"""
import random
import json
import csv
import os
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from flask import g
from database.db import db
from models.production import ProductionLine, Equipment, Sensor, ProductionTask, ProductionRecord, AlertRecord
from models.log import Log
from utils.response import Response


class DataSimulationService:
    """数据模拟服务类"""
    
    # 传感器类型配置
    SENSOR_TYPES = {
        'temperature': {'unit': '°C', 'min': 20, 'max': 80, 'threshold_low': 25, 'threshold_high': 75},
        'pressure': {'unit': 'psi', 'min': 0, 'max': 100, 'threshold_low': 10, 'threshold_high': 90},
        'humidity': {'unit': '%', 'min': 30, 'max': 90, 'threshold_low': 40, 'threshold_high': 80},
        'speed': {'unit': 'rpm', 'min': 0, 'max': 3000, 'threshold_low': 100, 'threshold_high': 2800},
        'vibration': {'unit': 'mm/s', 'min': 0, 'max': 10, 'threshold_low': 0.5, 'threshold_high': 8},
        'current': {'unit': 'A', 'min': 0, 'max': 50, 'threshold_low': 5, 'threshold_high': 45},
        'voltage': {'unit': 'V', 'min': 200, 'max': 400, 'threshold_low': 220, 'threshold_high': 380}
    }
    
    # 设备类型配置
    EQUIPMENT_TYPES = [
        '注塑机', '冲压机', '焊接机器人', '装配线', '包装机', 
        '检测设备', '输送带', '切割机', '喷涂设备', '烘干炉'
    ]
    
    # 生产线位置
    LOCATIONS = ['A车间', 'B车间', 'C车间', 'D车间', 'E车间', '中央仓库', '测试区']
    
    # 产品类型
    PRODUCTS = [
        {'name': '手机外壳', 'spec': 'A-001'},
        {'name': '汽车零件', 'spec': 'B-002'},
        {'name': '电子元件', 'spec': 'C-003'},
        {'name': '塑料制品', 'spec': 'D-004'},
        {'name': '金属配件', 'spec': 'E-005'}
    ]
    
    @staticmethod
    def generate_simulation_config():
        """生成默认模拟配置"""
        return {
            'lines': {
                'count': 3,
                'status_distribution': {'running': 0.6, 'stopped': 0.2, 'maintenance': 0.1, 'error': 0.1}
            },
            'equipments': {
                'per_line': 3,
                'status_distribution': {'running': 0.5, 'idle': 0.3, 'maintenance': 0.1, 'error': 0.05, 'offline': 0.05}
            },
            'sensors': {
                'per_equipment': 4,
                'types': ['temperature', 'pressure', 'humidity', 'speed', 'vibration', 'current', 'voltage'],
                'type_distribution': {'temperature': 0.3, 'pressure': 0.2, 'humidity': 0.15, 'speed': 0.15, 'vibration': 0.1, 'current': 0.05, 'voltage': 0.05},
                'data_distribution': 'normal'  # normal, uniform, random
            },
            'tasks': {
                'count': 10,
                'status_distribution': {'pending': 0.3, 'in_progress': 0.4, 'paused': 0.1, 'completed': 0.15, 'cancelled': 0.05}
            },
            'records': {
                'days': 7,
                'records_per_day': 100,
                'data_distribution': 'normal'  # normal, uniform, random
            },
            'alerts': {
                'probability': 0.05,  # 告警概率
                'severity_distribution': {'info': 0.4, 'warning': 0.4, 'error': 0.15, 'critical': 0.05}
            }
        }
    
    @staticmethod
    def simulate_production_data(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据配置生成模拟数据
        """
        result = {
            'lines_created': 0,
            'equipments_created': 0,
            'sensors_created': 0,
            'tasks_created': 0,
            'records_created': 0,
            'alerts_created': 0,
            'errors': []
        }
        
        try:
            # 1. 生成生产线
            lines = DataSimulationService._generate_lines(config['lines'])
            db.session.flush()  # 刷新以获取ID，但不提交
            result['lines_created'] = len(lines)
            
            # 2. 为每条生产线生成设备
            equipments = []
            for line in lines:
                line_equipments = DataSimulationService._generate_equipments(
                    line, config['equipments']
                )
                equipments.extend(line_equipments)
            db.session.flush()
            result['equipments_created'] = len(equipments)
            
            # 3. 为每个设备生成传感器
            sensors = []
            for equipment in equipments:
                equipment_sensors = DataSimulationService._generate_sensors(
                    equipment, config['sensors']
                )
                sensors.extend(equipment_sensors)
            db.session.flush()
            result['sensors_created'] = len(sensors)
            
            # 4. 生成生产任务
            tasks = DataSimulationService._generate_tasks(config['tasks'], lines)
            db.session.flush()
            result['tasks_created'] = len(tasks)
            
            # 5. 生成生产记录
            records = DataSimulationService._generate_records(
                config['records'], equipments, tasks
            )
            db.session.flush()
            result['records_created'] = len(records)
            
            # 6. 生成告警记录
            alerts = DataSimulationService._generate_alerts(
                config['alerts'], sensors, equipments
            )
            result['alerts_created'] = len(alerts)
            
            # 统一提交所有数据
            db.session.commit()
            
            # 记录操作日志
            Log.add_log(
                g.user_id, g.username, 'simulate', 'simulation',
                f'生成模拟数据: {result["lines_created"]}条生产线, {result["equipments_created"]}台设备, '
                f'{result["sensors_created"]}个传感器, {result["tasks_created"]}个任务, '
                f'{result["records_created"]}条记录, {result["alerts_created"]}条告警'
            )
            
            return Response.success(result, '模拟数据生成成功')
            
        except Exception as e:
            db.session.rollback()
            return Response.error(f'模拟数据生成失败: {str(e)}')
    
    @staticmethod
    def _generate_lines(config: Dict[str, Any]) -> List[ProductionLine]:
        """生成生产线数据"""
        lines = []
        line_statuses = list(config['status_distribution'].keys())
        line_weights = list(config['status_distribution'].values())
        
        for i in range(config['count']):
            # 使用时间戳确保唯一性
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            line_code = f'LINE-{timestamp}-{i+1}'
            line_name = f'生产线{i+1}'
            status = random.choices(line_statuses, weights=line_weights)[0]
            
            # 检查是否已存在
            existing = ProductionLine.query.filter_by(line_code=line_code).first()
            if existing:
                continue
            
            line = ProductionLine(
                line_code=line_code,
                line_name=line_name,
                description=f'模拟生产线{i+1}，位于{random.choice(DataSimulationService.LOCATIONS)}',
                status=status,
                capacity=random.randint(1000, 10000),
                location=random.choice(DataSimulationService.LOCATIONS),
                supervisor=f'负责人{i+1}'
            )
            db.session.add(line)
            lines.append(line)
        
        return lines
    
    @staticmethod
    def _generate_equipments(line: ProductionLine, config: Dict[str, Any]) -> List[Equipment]:
        """为生产线生成设备数据"""
        equipments = []
        equipment_statuses = list(config['status_distribution'].keys())
        equipment_weights = list(config['status_distribution'].values())
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        for i in range(config['per_line']):
            equipment_code = f'EQP-{timestamp}-{line.id}-{i+1}'
            equipment_name = f'{random.choice(DataSimulationService.EQUIPMENT_TYPES)}-{i+1}'
            status = random.choices(equipment_statuses, weights=equipment_weights)[0]
            
            # 检查是否已存在
            existing = Equipment.query.filter_by(equipment_code=equipment_code).first()
            if existing:
                continue
            
            # 根据状态生成模拟数据
            temperature = random.uniform(25, 75) if status == 'running' else random.uniform(20, 80)
            pressure = random.uniform(20, 80) if status == 'running' else random.uniform(0, 100)
            speed = random.uniform(500, 2500) if status == 'running' else 0
            
            equipment = Equipment(
                equipment_code=equipment_code,
                equipment_name=equipment_name,
                equipment_type=random.choice(DataSimulationService.EQUIPMENT_TYPES),
                line_id=line.id,
                status=status,
                model=f'MODEL-{random.randint(100, 999)}',
                manufacturer=random.choice(['厂商A', '厂商B', '厂商C', '厂商D']),
                purchase_date=datetime.now() - timedelta(days=random.randint(100, 1000)),
                install_date=datetime.now() - timedelta(days=random.randint(50, 500)),
                runtime_hours=random.uniform(100, 10000),
                temperature=temperature,
                pressure=pressure,
                speed=speed
            )
            db.session.add(equipment)
            equipments.append(equipment)
        
        return equipments
    
    @staticmethod
    def _generate_sensors(equipment: Equipment, config: Dict[str, Any]) -> List[Sensor]:
        """为设备生成传感器数据"""
        sensors = []
        # 防御性代码：确保type_distribution存在
        type_distribution = config.get('type_distribution', {})
        if not type_distribution:
            # 使用默认的传感器类型分布
            type_distribution = {sensor_type: 1.0/len(DataSimulationService.SENSOR_TYPES) 
                               for sensor_type in DataSimulationService.SENSOR_TYPES.keys()}
        
        sensor_types = list(type_distribution.keys())
        sensor_weights = list(type_distribution.values())
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        for i in range(config.get('per_equipment', 4)):
            sensor_type = random.choices(sensor_types, weights=sensor_weights)[0]
            sensor_config = DataSimulationService.SENSOR_TYPES.get(sensor_type, {})
            
            sensor_code = f'SEN-{timestamp}-{equipment.id}-{i+1}'
            sensor_name = f'{sensor_type}_sensor_{i+1}'
            
            # 检查是否已存在
            existing = Sensor.query.filter_by(sensor_code=sensor_code).first()
            if existing:
                continue
            
            # 生成模拟传感器值
            data_distribution = config.get('data_distribution', 'normal')
            if data_distribution == 'normal':
                # 正态分布
                mean = (sensor_config.get('min', 0) + sensor_config.get('max', 100)) / 2
                std = (sensor_config.get('max', 100) - sensor_config.get('min', 0)) / 6
                value = random.normalvariate(mean, std)
                value = max(sensor_config.get('min', 0), min(sensor_config.get('max', 100), value))
            elif data_distribution == 'uniform':
                # 均匀分布
                value = random.uniform(sensor_config.get('min', 0), sensor_config.get('max', 100))
            else:
                # 随机分布
                value = random.uniform(sensor_config.get('min', 0), sensor_config.get('max', 100))
            
            # 检查阈值
            status = 'normal'
            if sensor_config.get('threshold_low') and value < sensor_config['threshold_low']:
                status = 'warning'
            elif sensor_config.get('threshold_high') and value > sensor_config['threshold_high']:
                status = 'warning'
            
            sensor = Sensor(
                sensor_code=sensor_code,
                sensor_name=sensor_name,
                sensor_type=sensor_type,
                equipment_id=equipment.id,
                unit=sensor_config.get('unit', ''),
                min_value=sensor_config.get('min', 0),
                max_value=sensor_config.get('max', 100),
                threshold_low=sensor_config.get('threshold_low'),
                threshold_high=sensor_config.get('threshold_high'),
                status=status,
                last_value=value,
                last_read_time=datetime.now() - timedelta(minutes=random.randint(0, 60))
            )
            db.session.add(sensor)
            sensors.append(sensor)
        
        return sensors
    
    @staticmethod
    def _generate_tasks(config: Dict[str, Any], lines: List[ProductionLine]) -> List[ProductionTask]:
        """生成生产任务数据"""
        tasks = []
        # 防御性代码：确保status_distribution存在
        status_distribution = config.get('status_distribution', {})
        if not status_distribution:
            # 使用默认的任务状态分布
            status_distribution = {'pending': 0.3, 'in_progress': 0.4, 'paused': 0.1, 'completed': 0.15, 'cancelled': 0.05}
        
        task_statuses = list(status_distribution.keys())
        task_weights = list(status_distribution.values())
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        for i in range(config.get('count', 10)):
            task_code = f'TASK-{timestamp}-{i+1}'
            task_name = f'生产任务{i+1}'
            status = random.choices(task_statuses, weights=task_weights)[0]
            product = random.choice(DataSimulationService.PRODUCTS)
            
            # 检查是否已存在
            existing = ProductionTask.query.filter_by(task_code=task_code).first()
            if existing:
                continue
            
            # 根据状态设置时间
            now = datetime.now()
            if status == 'completed':
                start_time = now - timedelta(days=random.randint(1, 7))
                end_time = now - timedelta(hours=random.randint(1, 24))
                actual_start_time = start_time
                actual_end_time = end_time
                completed_quantity = random.randint(800, 1000)
            elif status == 'in_progress':
                start_time = now - timedelta(days=random.randint(1, 3))
                end_time = now + timedelta(days=random.randint(1, 3))
                actual_start_time = start_time
                actual_end_time = None
                completed_quantity = random.randint(300, 700)
            else:
                start_time = now + timedelta(days=random.randint(1, 7))
                end_time = now + timedelta(days=random.randint(8, 14))
                actual_start_time = None
                actual_end_time = None
                completed_quantity = 0
            
            task = ProductionTask(
                task_code=task_code,
                task_name=task_name,
                line_id=random.choice(lines).id if lines else None,
                product_name=product['name'],
                product_spec=product['spec'],
                quantity=1000,
                completed_quantity=completed_quantity,
                status=status,
                priority=random.randint(1, 10),
                start_time=start_time,
                end_time=end_time,
                actual_start_time=actual_start_time,
                actual_end_time=actual_end_time
            )
            db.session.add(task)
            tasks.append(task)
        
        return tasks
    
    @staticmethod
    def _generate_records(config: Dict[str, Any], equipments: List[Equipment], tasks: List[ProductionTask]) -> List[ProductionRecord]:
        """生成生产记录数据"""
        records = []
        
        for day in range(config['days']):
            record_date = datetime.now() - timedelta(days=day)
            
            for _ in range(config['records_per_day']):
                equipment = random.choice(equipments) if equipments else None
                task = random.choice(tasks) if tasks else None
                
                product_count = random.randint(50, 200)
                qualified_count = int(product_count * random.uniform(0.85, 0.99))
                defect_count = product_count - qualified_count
                yield_rate = qualified_count / product_count * 100 if product_count > 0 else 0
                
                record = ProductionRecord(
                    equipment_id=equipment.id if equipment else None,
                    task_id=task.id if task else None,
                    product_count=product_count,
                    qualified_count=qualified_count,
                    defect_count=defect_count,
                    yield_rate=yield_rate,
                    temperature=random.uniform(25, 75),
                    humidity=random.uniform(40, 80),
                    duration=random.randint(300, 3600),
                    efficiency=random.uniform(80, 99),
                    record_time=record_date - timedelta(minutes=random.randint(0, 1440))
                )
                db.session.add(record)
                records.append(record)
        
        return records
    
    @staticmethod
    def _generate_alerts(config: Dict[str, Any], sensors: List[Sensor], equipments: List[Equipment]) -> List[AlertRecord]:
        """生成告警记录数据"""
        alerts = []
        # 防御性代码：确保severity_distribution存在
        severity_distribution = config.get('severity_distribution', {})
        if not severity_distribution:
            # 使用默认的严重程度分布
            severity_distribution = {'info': 0.4, 'warning': 0.4, 'error': 0.15, 'critical': 0.05}
        
        severity_levels = list(severity_distribution.keys())
        severity_weights = list(severity_distribution.values())
        
        probability = config.get('probability', 0.05)
        
        for sensor in sensors:
            if random.random() < probability:
                severity = random.choices(severity_levels, weights=severity_weights)[0]
                alert = AlertRecord(
                    alert_code=f'ALERT-{datetime.now().strftime("%Y%m%d%H%M%S")}-{len(alerts)+1}',
                    alert_type='sensor_warning',
                    equipment_id=sensor.equipment_id,
                    sensor_id=sensor.id,
                    severity=severity,
                    message=f'{sensor.sensor_name}数值异常: {sensor.last_value}{sensor.unit}',
                    value=sensor.last_value,
                    threshold=sensor.threshold_high if sensor.last_value > (sensor.threshold_high or 0) else sensor.threshold_low,
                    status='active' if random.random() < 0.7 else 'acknowledged'
                )
                db.session.add(alert)
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def clear_simulation_data() -> Dict[str, Any]:
        """清除模拟数据"""
        try:
            # 删除相关记录（保留系统基础数据）
            deleted_counts = {
                'production_records': ProductionRecord.query.delete(),
                'alert_records': AlertRecord.query.delete(),
                'sensors': Sensor.query.delete(),
                'equipments': Equipment.query.delete(),
                'production_tasks': ProductionTask.query.delete(),
                'production_lines': ProductionLine.query.delete()
            }
            
            db.session.commit()
            
            Log.add_log(
                g.user_id, g.username, 'delete', 'simulation',
                f'清除模拟数据: {deleted_counts}'
            )
            
            return Response.success(deleted_counts, '模拟数据清除成功')
            
        except Exception as e:
            db.session.rollback()
            return Response.error(f'清除模拟数据失败: {str(e)}')
    
    @staticmethod
    def get_simulation_status() -> Dict[str, Any]:
        """获取当前模拟数据状态"""
        counts = {
            'production_lines': ProductionLine.query.count(),
            'equipments': Equipment.query.count(),
            'sensors': Sensor.query.count(),
            'production_tasks': ProductionTask.query.count(),
            'production_records': ProductionRecord.query.count(),
            'alert_records': AlertRecord.query.count()
        }
        
        # 统计状态分布
        line_status = {status: ProductionLine.query.filter_by(status=status).count() 
                      for status in ['running', 'stopped', 'maintenance', 'error']}
        equipment_status = {status: Equipment.query.filter_by(status=status).count() 
                          for status in ['running', 'idle', 'maintenance', 'error', 'offline']}
        sensor_status = {status: Sensor.query.filter_by(status=status).count() 
                        for status in ['normal', 'warning', 'error', 'offline']}
        task_status = {status: ProductionTask.query.filter_by(status=status).count() 
                      for status in ['pending', 'in_progress', 'paused', 'completed', 'cancelled']}
        
        return Response.success({
            'counts': counts,
            'status_distribution': {
                'lines': line_status,
                'equipments': equipment_status,
                'sensors': sensor_status,
                'tasks': task_status
            }
        })
    
    # ==================== 文件导入功能 ====================
    
    @staticmethod
    def import_csv_data(file_path: str, data_type: str) -> Dict[str, Any]:
        """
        导入CSV文件数据
        :param file_path: CSV文件路径
        :param data_type: 数据类型 production_line, equipment, sensor, task, record, alert
        :return: 导入结果
        """
        try:
            import_count = 0
            errors = []
            
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # 根据数据类型处理行数据
                        if data_type == 'production_line':
                            obj = DataSimulationService._create_production_line_from_csv(row)
                        elif data_type == 'equipment':
                            obj = DataSimulationService._create_equipment_from_csv(row)
                        elif data_type == 'sensor':
                            obj = DataSimulationService._create_sensor_from_csv(row)
                        elif data_type == 'task':
                            obj = DataSimulationService._create_task_from_csv(row)
                        else:
                            errors.append(f'第{row_num}行: 不支持的数据类型 {data_type}')
                            continue
                        
                        if obj:
                            db.session.add(obj)
                            import_count += 1
                            
                    except Exception as e:
                        errors.append(f'第{row_num}行: {str(e)}')
                
                db.session.commit()
            
            # 记录操作日志
            Log.add_log(
                g.user_id, g.username, 'import', 'simulation',
                f'导入CSV数据: {data_type}, 成功 {import_count} 条'
            )
            
            return Response.success({
                'imported_count': import_count,
                'error_count': len(errors),
                'errors': errors
            }, f'成功导入 {import_count} 条数据')
            
        except Exception as e:
            db.session.rollback()
            return Response.error(f'导入CSV文件失败: {str(e)}')
    
    @staticmethod
    def import_json_data(file_path: str, data_type: str) -> Dict[str, Any]:
        """
        导入JSON文件数据
        :param file_path: JSON文件路径
        :param data_type: 数据类型 record, alert
        :return: 导入结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            import_count = 0
            errors = []
            
            # 处理数据
            if isinstance(data, list):
                for item_num, item in enumerate(data, 1):
                    try:
                        if data_type == 'record':
                            obj = DataSimulationService._create_record_from_json(item)
                        elif data_type == 'alert':
                            obj = DataSimulationService._create_alert_from_json(item)
                        else:
                            errors.append(f'第{item_num}项: 不支持的数据类型 {data_type}')
                            continue
                        
                        if obj:
                            db.session.add(obj)
                            import_count += 1
                            
                    except Exception as e:
                        errors.append(f'第{item_num}项: {str(e)}')
            else:
                return Response.error('JSON数据必须是数组格式')
            
            db.session.commit()
            
            # 记录操作日志
            Log.add_log(
                g.user_id, g.username, 'import', 'simulation',
                f'导入JSON数据: {data_type}, 成功 {import_count} 条'
            )
            
            return Response.success({
                'imported_count': import_count,
                'error_count': len(errors),
                'errors': errors
            }, f'成功导入 {import_count} 条数据')
            
        except Exception as e:
            db.session.rollback()
            return Response.error(f'导入JSON文件失败: {str(e)}')
    
    # ==================== 数据创建方法 ====================
    
    @staticmethod
    def _create_production_line_from_csv(row: Dict) -> Optional[ProductionLine]:
        """从CSV行创建生产线"""
        required_fields = ['line_code', 'line_name', 'status']
        for field in required_fields:
            if field not in row:
                raise ValueError(f'缺少必填字段: {field}')
        
        line = ProductionLine(
            line_code=row['line_code'],
            line_name=row['line_name'],
            description=row.get('description', ''),
            status=row['status'],
            capacity=int(row.get('capacity', 1000)),
            location=row.get('location', ''),
            supervisor=row.get('supervisor', '')
        )
        return line
    
    @staticmethod
    def _create_equipment_from_csv(row: Dict) -> Optional[Equipment]:
        """从CSV行创建设备"""
        required_fields = ['equipment_code', 'equipment_name', 'equipment_type', 'line_id', 'status']
        for field in required_fields:
            if field not in row:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证生产线ID是否存在
        line = ProductionLine.query.get(int(row['line_id']))
        if not line:
            raise ValueError(f'生产线ID {row["line_id"]} 不存在')
        
        equipment = Equipment(
            equipment_code=row['equipment_code'],
            equipment_name=row['equipment_name'],
            equipment_type=row['equipment_type'],
            line_id=int(row['line_id']),
            status=row['status'],
            model=row.get('model', ''),
            manufacturer=row.get('manufacturer', ''),
            purchase_date=datetime.strptime(row['purchase_date'], '%Y-%m-%d') if row.get('purchase_date') else None,
            install_date=datetime.strptime(row['install_date'], '%Y-%m-%d') if row.get('install_date') else None,
            runtime_hours=float(row.get('runtime_hours', 0)),
            temperature=float(row.get('temperature', 25)),
            pressure=float(row.get('pressure', 50)),
            speed=float(row.get('speed', 0))
        )
        return equipment
    
    @staticmethod
    def _create_sensor_from_csv(row: Dict) -> Optional[Sensor]:
        """从CSV行创建传感器"""
        required_fields = ['sensor_code', 'sensor_name', 'sensor_type', 'equipment_id']
        for field in required_fields:
            if field not in row:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证设备ID是否存在
        equipment = Equipment.query.get(int(row['equipment_id']))
        if not equipment:
            raise ValueError(f'设备ID {row["equipment_id"]} 不存在')
        
        sensor = Sensor(
            sensor_code=row['sensor_code'],
            sensor_name=row['sensor_name'],
            sensor_type=row['sensor_type'],
            equipment_id=int(row['equipment_id']),
            unit=row.get('unit', ''),
            min_value=float(row.get('min_value', 0)),
            max_value=float(row.get('max_value', 100)),
            threshold_low=float(row.get('threshold_low')) if row.get('threshold_low') else None,
            threshold_high=float(row.get('threshold_high')) if row.get('threshold_high') else None,
            status=row.get('status', 'normal'),
            last_value=float(row.get('last_value', 50)),
            last_read_time=datetime.strptime(row['last_read_time'], '%Y-%m-%d %H:%M:%S') if row.get('last_read_time') else datetime.now()
        )
        return sensor
    
    @staticmethod
    def _create_task_from_csv(row: Dict) -> Optional[ProductionTask]:
        """从CSV行创建生产任务"""
        required_fields = ['task_code', 'task_name', 'product_name', 'product_spec', 'quantity', 'status']
        for field in required_fields:
            if field not in row:
                raise ValueError(f'缺少必填字段: {field}')
        
        task = ProductionTask(
            task_code=row['task_code'],
            task_name=row['task_name'],
            line_id=int(row['line_id']) if row.get('line_id') else None,
            product_name=row['product_name'],
            product_spec=row['product_spec'],
            quantity=int(row['quantity']),
            completed_quantity=int(row.get('completed_quantity', 0)),
            status=row['status'],
            priority=int(row.get('priority', 5)),
            start_time=datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M:%S') if row.get('start_time') else None,
            end_time=datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M:%S') if row.get('end_time') else None,
            actual_start_time=datetime.strptime(row['actual_start_time'], '%Y-%m-%d %H:%M:%S') if row.get('actual_start_time') else None,
            actual_end_time=datetime.strptime(row['actual_end_time'], '%Y-%m-%d %H:%M:%S') if row.get('actual_end_time') else None
        )
        return task
    
    @staticmethod
    def _create_record_from_json(item: Dict) -> Optional[ProductionRecord]:
        """从JSON项创建生产记录"""
        required_fields = ['equipment_id', 'product_count', 'qualified_count', 'defect_count']
        for field in required_fields:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证设备ID是否存在
        if item['equipment_id']:
            equipment = Equipment.query.get(int(item['equipment_id']))
            if not equipment:
                raise ValueError(f'设备ID {item["equipment_id"]} 不存在')
        
        # 验证任务ID是否存在
        if item.get('task_id'):
            task = ProductionTask.query.get(int(item['task_id']))
            if not task:
                raise ValueError(f'任务ID {item["task_id"]} 不存在')
        
        record = ProductionRecord(
            equipment_id=int(item['equipment_id']) if item['equipment_id'] else None,
            task_id=int(item['task_id']) if item.get('task_id') else None,
            product_count=int(item['product_count']),
            qualified_count=int(item['qualified_count']),
            defect_count=int(item['defect_count']),
            yield_rate=float(item.get('yield_rate', 0)),
            temperature=float(item.get('temperature', 25)),
            humidity=float(item.get('humidity', 50)),
            duration=int(item.get('duration', 300)),
            efficiency=float(item.get('efficiency', 90)),
            record_time=datetime.strptime(item['record_time'], '%Y-%m-%d %H:%M:%S') if item.get('record_time') else datetime.now()
        )
        return record
    
    @staticmethod
    def _create_alert_from_json(item: Dict) -> Optional[AlertRecord]:
        """从JSON项创建告警记录"""
        required_fields = ['alert_code', 'alert_type', 'severity', 'message']
        for field in required_fields:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证设备ID是否存在
        if item.get('equipment_id'):
            equipment = Equipment.query.get(int(item['equipment_id']))
            if not equipment:
                raise ValueError(f'设备ID {item["equipment_id"]} 不存在')
        
        # 验证传感器ID是否存在
        if item.get('sensor_id'):
            sensor = Sensor.query.get(int(item['sensor_id']))
            if not sensor:
                raise ValueError(f'传感器ID {item["sensor_id"]} 不存在')
        
        alert = AlertRecord(
            alert_code=item['alert_code'],
            alert_type=item['alert_type'],
            equipment_id=int(item['equipment_id']) if item.get('equipment_id') else None,
            sensor_id=int(item['sensor_id']) if item.get('sensor_id') else None,
            severity=item['severity'],
            message=item['message'],
            value=float(item.get('value', 0)),
            threshold=float(item.get('threshold', 0)),
            status=item.get('status', 'active'),
            resolved_time=datetime.strptime(item['resolved_time'], '%Y-%m-%d %H:%M:%S') if item.get('resolved_time') else None,
            resolved_notes=item.get('resolved_notes', '')
        )
        return alert
    
    # ==================== 数据验证方法 ====================
    
    @staticmethod
    def validate_data(data_type: str, data: List[Dict]) -> Dict[str, Any]:
        """
        验证数据完整性
        :param data_type: 数据类型
        :param data: 数据列表
        :return: 验证结果
        """
        validation_results = {
            'total_count': len(data),
            'valid_count': 0,
            'invalid_count': 0,
            'errors': []
        }
        
        for i, item in enumerate(data):
            try:
                if data_type == 'production_line':
                    DataSimulationService._validate_production_line(item)
                elif data_type == 'equipment':
                    DataSimulationService._validate_equipment(item)
                elif data_type == 'sensor':
                    DataSimulationService._validate_sensor(item)
                elif data_type == 'task':
                    DataSimulationService._validate_task(item)
                elif data_type == 'record':
                    DataSimulationService._validate_record(item)
                elif data_type == 'alert':
                    DataSimulationService._validate_alert(item)
                else:
                    validation_results['errors'].append(f'第{i+1}项: 不支持的数据类型 {data_type}')
                    validation_results['invalid_count'] += 1
                    continue
                
                validation_results['valid_count'] += 1
                
            except Exception as e:
                validation_results['errors'].append(f'第{i+1}项: {str(e)}')
                validation_results['invalid_count'] += 1
        
        return validation_results
    
    @staticmethod
    def _validate_production_line(item: Dict):
        """验证生产线数据"""
        required = ['line_code', 'line_name', 'status']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证状态
        valid_statuses = ['running', 'stopped', 'maintenance', 'error']
        if item['status'] not in valid_statuses:
            raise ValueError(f'状态必须是: {", ".join(valid_statuses)}')
        
        # 验证唯一性
        existing = ProductionLine.query.filter_by(line_code=item['line_code']).first()
        if existing:
            raise ValueError(f'生产线编号 {item["line_code"]} 已存在')
    
    @staticmethod
    def _validate_equipment(item: Dict):
        """验证设备数据"""
        required = ['equipment_code', 'equipment_name', 'equipment_type', 'line_id', 'status']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证状态
        valid_statuses = ['running', 'idle', 'maintenance', 'error', 'offline']
        if item['status'] not in valid_statuses:
            raise ValueError(f'状态必须是: {", ".join(valid_statuses)}')
        
        # 验证生产线存在
        if not ProductionLine.query.get(int(item['line_id'])):
            raise ValueError(f'生产线ID {item["line_id"]} 不存在')
        
        # 验证唯一性
        existing = Equipment.query.filter_by(equipment_code=item['equipment_code']).first()
        if existing:
            raise ValueError(f'设备编号 {item["equipment_code"]} 已存在')
    
    @staticmethod
    def _validate_sensor(item: Dict):
        """验证传感器数据"""
        required = ['sensor_code', 'sensor_name', 'sensor_type', 'equipment_id']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证设备存在
        if not Equipment.query.get(int(item['equipment_id'])):
            raise ValueError(f'设备ID {item["equipment_id"]} 不存在')
        
        # 验证传感器类型
        valid_types = list(DataSimulationService.SENSOR_TYPES.keys())
        if item['sensor_type'] not in valid_types:
            raise ValueError(f'传感器类型必须是: {", ".join(valid_types)}')
        
        # 验证唯一性
        existing = Sensor.query.filter_by(sensor_code=item['sensor_code']).first()
        if existing:
            raise ValueError(f'传感器编号 {item["sensor_code"]} 已存在')
    
    @staticmethod
    def _validate_task(item: Dict):
        """验证生产任务数据"""
        required = ['task_code', 'task_name', 'product_name', 'product_spec', 'quantity', 'status']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证状态
        valid_statuses = ['pending', 'in_progress', 'paused', 'completed', 'cancelled']
        if item['status'] not in valid_statuses:
            raise ValueError(f'状态必须是: {", ".join(valid_statuses)}')
        
        # 验证生产线存在（如果提供了line_id）
        if item.get('line_id') and not ProductionLine.query.get(int(item['line_id'])):
            raise ValueError(f'生产线ID {item["line_id"]} 不存在')
        
        # 验证唯一性
        existing = ProductionTask.query.filter_by(task_code=item['task_code']).first()
        if existing:
            raise ValueError(f'任务编号 {item["task_code"]} 已存在')
    
    @staticmethod
    def _validate_record(item: Dict):
        """验证生产记录数据"""
        required = ['equipment_id', 'product_count', 'qualified_count', 'defect_count']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证设备存在
        if item['equipment_id'] and not Equipment.query.get(int(item['equipment_id'])):
            raise ValueError(f'设备ID {item["equipment_id"]} 不存在')
        
        # 验证任务存在（如果提供了task_id）
        if item.get('task_id') and not ProductionTask.query.get(int(item['task_id'])):
            raise ValueError(f'任务ID {item["task_id"]} 不存在')
        
        # 验证数值范围
        if int(item['product_count']) <= 0:
            raise ValueError('产品数量必须大于0')
        
        if int(item['qualified_count']) < 0:
            raise ValueError('合格数量不能为负数')
        
        if int(item['defect_count']) < 0:
            raise ValueError('缺陷数量不能为负数')
    
    @staticmethod
    def _validate_alert(item: Dict):
        """验证告警记录数据"""
        required = ['alert_code', 'alert_type', 'severity', 'message']
        for field in required:
            if field not in item:
                raise ValueError(f'缺少必填字段: {field}')
        
        # 验证严重程度
        valid_severities = ['info', 'warning', 'error', 'critical']
        if item['severity'] not in valid_severities:
            raise ValueError(f'严重程度必须是: {", ".join(valid_severities)}')
        
        # 验证设备存在（如果提供了equipment_id）
        if item.get('equipment_id') and not Equipment.query.get(int(item['equipment_id'])):
            raise ValueError(f'设备ID {item["equipment_id"]} 不存在')
        
        # 验证传感器存在（如果提供了sensor_id）
        if item.get('sensor_id') and not Sensor.query.get(int(item['sensor_id'])):
            raise ValueError(f'传感器ID {item["sensor_id"]} 不存在')
        
        # 验证唯一性
        existing = AlertRecord.query.filter_by(alert_code=item['alert_code']).first()
        if existing:
            raise ValueError(f'告警编号 {item["alert_code"]} 已存在')
    
    # ==================== 模拟数据源功能 ====================
    
    @staticmethod
    def create_mock_data_source(source_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建模拟数据源
        :param source_type: 数据源类型 api, websocket, file_stream, user_input
        :param config: 配置参数
        :return: 创建结果
        """
        try:
            source_id = f'{source_type}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
            if source_type == 'api':
                # 模拟API数据源
                result = {
                    'source_id': source_id,
                    'type': 'api',
                    'endpoint': config.get('endpoint', '/mock/api/data'),
                    'method': config.get('method', 'GET'),
                    'interval': config.get('interval', 5),  # 秒
                    'description': '模拟API数据源，定期生成数据'
                }
                
            elif source_type == 'websocket':
                # 模拟WebSocket数据源
                result = {
                    'source_id': source_id,
                    'type': 'websocket',
                    'url': config.get('url', 'ws://localhost:5001/mock/ws'),
                    'interval': config.get('interval', 1),  # 秒
                    'description': '模拟WebSocket数据源，实时推送数据'
                }
                
            elif source_type == 'file_stream':
                # 模拟文件流数据源
                result = {
                    'source_id': source_id,
                    'type': 'file_stream',
                    'file_path': config.get('file_path', ''),
                    'format': config.get('format', 'csv'),
                    'interval': config.get('interval', 10),  # 秒
                    'description': '模拟文件流数据源，从文件读取数据'
                }
                
            elif source_type == 'user_input':
                # 模拟用户输入数据源
                result = {
                    'source_id': source_id,
                    'type': 'user_input',
                    'form_config': config.get('form_config', {}),
                    'description': '模拟用户输入数据源，收集用户输入数据'
                }
                
            else:
                return Response.error(f'不支持的数据源类型: {source_type}')
            
            # 记录操作日志
            Log.add_log(
                g.user_id, g.username, 'create', 'simulation',
                f'创建模拟数据源: {source_type} ({source_id})'
            )
            
            return Response.success(result, '模拟数据源创建成功')
            
        except Exception as e:
            return Response.error(f'创建模拟数据源失败: {str(e)}')
    
    @staticmethod
    def generate_mock_data_from_source(source_id: str, count: int = 10) -> Dict[str, Any]:
        """
        从模拟数据源生成数据
        :param source_id: 数据源ID
        :param count: 生成数据条数
        :return: 生成结果
        """
        try:
            # 根据数据源类型生成模拟数据
            if source_id.startswith('api_'):
                data = DataSimulationService._generate_api_mock_data(count)
                data_type = 'api_data'
            elif source_id.startswith('websocket_'):
                data = DataSimulationService._generate_websocket_mock_data(count)
                data_type = 'websocket_data'
            elif source_id.startswith('file_stream_'):
                data = DataSimulationService._generate_file_stream_mock_data(count)
                data_type = 'file_stream_data'
            elif source_id.startswith('user_input_'):
                data = DataSimulationService._generate_user_input_mock_data(count)
                data_type = 'user_input_data'
            else:
                return Response.error(f'未知的数据源类型: {source_id}')
            
            # 记录操作日志
            Log.add_log(
                g.user_id, g.username, 'generate', 'simulation',
                f'从数据源 {source_id} 生成数据: {len(data)} 条'
            )
            
            return Response.success({
                'source_id': source_id,
                'data_type': data_type,
                'generated_count': len(data),
                'data': data[:5]  # 只返回前5条作为示例
            }, f'成功从数据源生成 {len(data)} 条数据')
            
        except Exception as e:
            return Response.error(f'从数据源生成数据失败: {str(e)}')
    
    @staticmethod
    def _generate_api_mock_data(count: int) -> List[Dict]:
        """生成API模拟数据"""
        data = []
        for i in range(count):
            data.append({
                'id': f'api_data_{i+1}',
                'timestamp': datetime.now().isoformat(),
                'value': random.uniform(0, 100),
                'status': random.choice(['success', 'error', 'pending']),
                'response_time': random.uniform(0.1, 2.0)
            })
        return data
    
    @staticmethod
    def _generate_websocket_mock_data(count: int) -> List[Dict]:
        """生成WebSocket模拟数据"""
        data = []
        for i in range(count):
            data.append({
                'id': f'ws_data_{i+1}',
                'timestamp': datetime.now().isoformat(),
                'sensor_id': f'sensor_{random.randint(1, 100)}',
                'value': random.uniform(0, 100),
                'unit': random.choice(['°C', 'psi', '%', 'rpm', 'mm/s', 'A', 'V']),
                'status': random.choice(['normal', 'warning', 'error'])
            })
        return data
    
    @staticmethod
    def _generate_file_stream_mock_data(count: int) -> List[Dict]:
        """生成文件流模拟数据"""
        data = []
        for i in range(count):
            data.append({
                'id': f'file_data_{i+1}',
                'timestamp': datetime.now().isoformat(),
                'line_number': i + 1,
                'content': f'模拟文件数据行 {i+1}',
                'file_size': random.randint(100, 10000),
                'checksum': f'checksum_{random.randint(1000, 9999)}'
            })
        return data
    
    @staticmethod
    def _generate_user_input_mock_data(count: int) -> List[Dict]:
        """生成用户输入模拟数据"""
        data = []
        for i in range(count):
            data.append({
                'id': f'user_data_{i+1}',
                'timestamp': datetime.now().isoformat(),
                'user_id': f'user_{random.randint(1, 100)}',
                'input_type': random.choice(['text', 'number', 'select', 'checkbox']),
                'value': f'用户输入值 {i+1}',
                'validation_result': random.choice(['valid', 'invalid'])
            })
        return data