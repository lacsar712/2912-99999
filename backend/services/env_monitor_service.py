"""
环境监测服务模块
"""
from datetime import datetime, timedelta
from database.db import db
from models.env_monitor import EnvArea, EnvMonitorPoint, EnvReading, EnvStandard
from models.production import AlertRecord
from utils.response import Response
from utils.validator import Validator
import random


class EnvMonitorService:
    """环境监测服务类"""

    # ==================== 区域管理 ====================

    @staticmethod
    def get_area_tree():
        """获取区域树结构"""
        areas = EnvArea.query.filter_by(status=1, is_active=True).order_by(EnvArea.sort_order).all()
        area_dict = {area.id: area.to_dict() for area in areas}
        
        root_areas = []
        for area in areas:
            if area.parent_id is None:
                root_areas.append(area_dict[area.id])
            else:
                parent = area_dict.get(area.parent_id)
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(area_dict[area.id])
        
        return Response.success(root_areas)

    @staticmethod
    def get_areas(page=1, size=20, parent_id=None):
        """获取区域列表"""
        query = EnvArea.query.filter_by(status=1)
        
        if parent_id is not None:
            if parent_id == 0:
                query = query.filter(EnvArea.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
        
        pagination = query.order_by(EnvArea.sort_order, EnvArea.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        items = [area.to_dict() for area in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_area_by_id(area_id):
        """获取区域详情"""
        area = EnvArea.get_by_id(area_id)
        if not area:
            return Response.not_found('区域不存在')
        return Response.success(area.to_dict())

    @staticmethod
    def create_area(data):
        """创建区域"""
        validation = Validator.validate_form(data, {
            'area_code': ['required'],
            'area_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        
        if EnvArea.query.filter_by(area_code=data['area_code'], status=1).first():
            return Response.bad_request('区域编码已存在')
        
        if data.get('parent_id'):
            parent = EnvArea.get_by_id(data['parent_id'])
            if not parent:
                return Response.bad_request('父区域不存在')
        
        area = EnvArea(
            area_code=data['area_code'],
            area_name=data['area_name'],
            parent_id=data.get('parent_id'),
            area_type=data.get('area_type', 'other'),
            description=data.get('description', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        area.save()
        
        return Response.success(area.to_dict(), '区域创建成功')

    @staticmethod
    def update_area(area_id, data):
        """更新区域"""
        area = EnvArea.get_by_id(area_id)
        if not area:
            return Response.not_found('区域不存在')
        
        if 'area_code' in data and data['area_code'] != area.area_code:
            if EnvArea.query.filter(EnvArea.area_code == data['area_code'], EnvArea.id != area_id, EnvArea.status == 1).first():
                return Response.bad_request('区域编码已存在')
        
        if data.get('parent_id') and data['parent_id'] != area.parent_id:
            parent = EnvArea.get_by_id(data['parent_id'])
            if not parent:
                return Response.bad_request('父区域不存在')
        
        area.update(
            area_code=data.get('area_code', area.area_code),
            area_name=data.get('area_name', area.area_name),
            parent_id=data.get('parent_id', area.parent_id),
            area_type=data.get('area_type', area.area_type),
            description=data.get('description', area.description),
            sort_order=data.get('sort_order', area.sort_order),
            is_active=data.get('is_active', area.is_active)
        )
        
        return Response.success(area.to_dict(), '区域更新成功')

    @staticmethod
    def delete_area(area_id):
        """删除区域"""
        area = EnvArea.get_by_id(area_id)
        if not area:
            return Response.not_found('区域不存在')
        
        # 检查是否有子区域
        if EnvArea.query.filter_by(parent_id=area_id, status=1).count() > 0:
            return Response.bad_request('该区域下存在子区域，无法删除')
        
        # 检查是否有关联监测点
        if EnvMonitorPoint.query.filter_by(area_id=area_id, status=1).count() > 0:
            return Response.bad_request('该区域下存在监测点，无法删除')
        
        area.delete()
        return Response.success(message='区域删除成功')

    # ==================== 监测点管理 ====================

    @staticmethod
    def get_monitor_points(page=1, size=20, area_id=None, point_status=None):
        """获取监测点列表"""
        query = EnvMonitorPoint.query.filter_by(status=1)
        
        if area_id:
            query = query.filter_by(area_id=area_id)
        if point_status:
            query = query.filter_by(point_status=point_status)
        
        pagination = query.order_by(EnvMonitorPoint.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        items = [point.to_dict() for point in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_monitor_point_by_id(point_id):
        """获取监测点详情"""
        point = EnvMonitorPoint.get_by_id(point_id)
        if not point:
            return Response.not_found('监测点不存在')
        return Response.success(point.to_dict())

    @staticmethod
    def create_monitor_point(data):
        """创建监测点"""
        validation = Validator.validate_form(data, {
            'point_code': ['required'],
            'point_name': ['required'],
            'area_id': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        
        if EnvMonitorPoint.query.filter_by(point_code=data['point_code'], status=1).first():
            return Response.bad_request('监测点编号已存在')
        
        area = EnvArea.get_by_id(data['area_id'])
        if not area:
            return Response.bad_request('关联区域不存在')
        
        point = EnvMonitorPoint(
            point_code=data['point_code'],
            point_name=data['point_name'],
            area_id=data['area_id'],
            point_status=data.get('point_status', 'active'),
            location=data.get('location', ''),
            description=data.get('description', '')
        )
        
        if 'monitor_items' in data:
            point.set_monitor_items(data['monitor_items'])
        
        point.save()
        
        return Response.success(point.to_dict(), '监测点创建成功')

    @staticmethod
    def update_monitor_point(point_id, data):
        """更新监测点"""
        point = EnvMonitorPoint.get_by_id(point_id)
        if not point:
            return Response.not_found('监测点不存在')
        
        if 'point_code' in data and data['point_code'] != point.point_code:
            if EnvMonitorPoint.query.filter(EnvMonitorPoint.point_code == data['point_code'], EnvMonitorPoint.id != point_id, EnvMonitorPoint.status == 1).first():
                return Response.bad_request('监测点编号已存在')
        
        if 'area_id' in data and data['area_id'] != point.area_id:
            area = EnvArea.get_by_id(data['area_id'])
            if not area:
                return Response.bad_request('关联区域不存在')
        
        if 'monitor_items' in data:
            point.set_monitor_items(data['monitor_items'])
        
        point.update(
            point_code=data.get('point_code', point.point_code),
            point_name=data.get('point_name', point.point_name),
            area_id=data.get('area_id', point.area_id),
            point_status=data.get('point_status', point.point_status),
            location=data.get('location', point.location),
            description=data.get('description', point.description)
        )
        
        return Response.success(point.to_dict(), '监测点更新成功')

    @staticmethod
    def delete_monitor_point(point_id):
        """删除监测点"""
        point = EnvMonitorPoint.get_by_id(point_id)
        if not point:
            return Response.not_found('监测点不存在')
        
        # 删除关联读数
        EnvReading.query.filter_by(point_id=point_id).delete()
        
        point.delete()
        return Response.success(message='监测点删除成功')

    # ==================== 读数管理 ====================

    @staticmethod
    def add_reading(data):
        """添加监测读数"""
        validation = Validator.validate_form(data, {
            'point_id': ['required'],
            'item_name': ['required'],
            'item_value': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        
        point = EnvMonitorPoint.get_by_id(data['point_id'])
        if not point:
            return Response.bad_request('监测点不存在')
        
        # 检查项目是否在监测点配置中
        monitor_items = point.get_monitor_items()
        item_config = next((item for item in monitor_items if item['name'] == data['item_name']), None)
        item_unit = item_config['unit'] if item_config else data.get('item_unit', '')
        
        # 检查是否有对应的环境标准
        standard = EnvStandard.query.filter_by(item_name=data['item_name'], status=1).first()
        is_normal = True
        if standard:
            status, _ = standard.check_value(float(data['item_value']))
            is_normal = status == 'normal'
        
        reading = EnvReading(
            point_id=data['point_id'],
            item_name=data['item_name'],
            item_value=float(data['item_value']),
            item_unit=item_unit,
            read_time=data.get('read_time') or datetime.now(),
            is_normal=is_normal
        )
        reading.save()
        
        # 检查阈值并生成告警
        if standard and not is_normal:
            status, message = standard.check_value(float(data['item_value']))
            EnvMonitorService._generate_alert(point, data['item_name'], float(data['item_value']), standard, status, message)
        
        return Response.success(reading.to_dict(), '读数添加成功')

    @staticmethod
    def batch_add_readings(readings):
        """批量添加监测读数"""
        results = []
        errors = []
        
        for idx, reading_data in enumerate(readings):
            try:
                result = EnvMonitorService.add_reading(reading_data)
                if result.code == 200:
                    results.append(result.data)
                else:
                    errors.append(f'第{idx+1}条: {result.message}')
            except Exception as e:
                errors.append(f'第{idx+1}条: {str(e)}')
        
        return Response.success({
            'success_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        }, f'批量添加完成，成功{len(results)}条，失败{len(errors)}条')

    @staticmethod
    def _generate_alert(point, item_name, value, standard, status, message):
        """生成环境异常告警"""
        now = datetime.now()
        alert_code = f"ENV-ALERT-{now.strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        severity = 'warning'
        if status == 'danger':
            severity = standard.severity if standard.severity else 'error'
        
        # 检查最近是否已有相同告警（避免重复告警）
        recent_alert = AlertRecord.query.filter(
            AlertRecord.alert_type == 'env_abnormal',
            AlertRecord.status == 'active',
            AlertRecord.message.like(f'%{point.point_name}%{item_name}%')
        ).order_by(AlertRecord.create_time.desc()).first()
        
        if recent_alert and (now - recent_alert.create_time).total_seconds() < 300:
            return
        
        alert = AlertRecord(
            alert_code=alert_code,
            alert_type='env_abnormal',
            equipment_id=None,
            sensor_id=None,
            severity=severity,
            message=f'【{point.area.area_name if point.area else ""}】{point.point_name} - {item_name}异常: {message}',
            value=value,
            threshold=standard.alert_high if value > (standard.alert_high or 0) else standard.alert_low,
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

    @staticmethod
    def get_realtime_readings(area_id=None, point_id=None):
        """获取实时读数 - 按区域聚合展示每个监测点每个项目的最新读数"""
        query = EnvMonitorPoint.query.filter_by(status=1, point_status='active')
        
        if area_id:
            query = query.filter_by(area_id=area_id)
        if point_id:
            query = query.filter_by(id=point_id)
        
        points = query.all()
        
        result = {}
        for point in points:
            area_key = str(point.area_id)
            if area_key not in result:
                result[area_key] = {
                    'area_id': point.area_id,
                    'area_name': point.area.area_name if point.area else '',
                    'points': {}
                }
            
            point_data = {
                'point_id': point.id,
                'point_code': point.point_code,
                'point_name': point.point_name,
                'items': {}
            }
            
            monitor_items = point.get_monitor_items()
            for item in monitor_items:
                # 获取该监测点该项目的最新读数
                latest_reading = EnvReading.query.filter_by(
                    point_id=point.id,
                    item_name=item['name']
                ).order_by(EnvReading.read_time.desc()).first()
                
                # 获取标准
                standard = EnvStandard.query.filter_by(item_name=item['name'], status=1).first()
                
                item_data = {
                    'name': item['name'],
                    'unit': item['unit'],
                    'value': float(latest_reading.item_value) if latest_reading else None,
                    'read_time': latest_reading.read_time.strftime('%Y-%m-%d %H:%M:%S') if latest_reading else None,
                    'is_normal': latest_reading.is_normal if latest_reading else None,
                    'status': 'offline',
                    'standard': None
                }
                
                if standard and latest_reading:
                    status, status_msg = standard.check_value(float(latest_reading.item_value))
                    item_data['status'] = status
                    item_data['status_msg'] = status_msg
                    item_data['standard'] = {
                        'safety_low': float(standard.safety_low) if standard.safety_low else None,
                        'safety_high': float(standard.safety_high) if standard.safety_high else None,
                        'alert_low': float(standard.alert_low) if standard.alert_low else None,
                        'alert_high': float(standard.alert_high) if standard.alert_high else None
                    }
                
                point_data['items'][item['name']] = item_data
            
            result[area_key]['points'][str(point.id)] = point_data
        
        return Response.success(result)

    # ==================== 历史趋势查询 ====================

    @staticmethod
    def get_history_trend(area_id, item_names, time_window='1h', point_id=None):
        """
        获取历史趋势数据（按区域聚合）
        time_window: 1h/6h/24h/7d
        """
        # 计算时间范围
        now = datetime.now()
        if time_window == '1h':
            start_time = now - timedelta(hours=1)
        elif time_window == '6h':
            start_time = now - timedelta(hours=6)
        elif time_window == '24h':
            start_time = now - timedelta(hours=24)
        elif time_window == '7d':
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=1)
        
        # 获取该区域下的所有监测点
        point_query = EnvMonitorPoint.query.filter_by(status=1, area_id=area_id)
        if point_id:
            point_query = point_query.filter_by(id=point_id)
        points = point_query.all()
        
        point_ids = [p.id for p in points]
        if not point_ids:
            return Response.success({
                'time_window': time_window,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'item_names': item_names,
                'data': []
            })
        
        # 按项目查询读数
        result_data = {}
        for item_name in item_names:
            readings = EnvReading.query.filter(
                EnvReading.point_id.in_(point_ids),
                EnvReading.item_name == item_name,
                EnvReading.read_time >= start_time,
                EnvReading.read_time <= now
            ).order_by(EnvReading.read_time.asc()).all()
            
            # 按时间聚合（同一时间点取平均值）
            time_aggregated = {}
            for reading in readings:
                time_key = reading.read_time.strftime('%Y-%m-%d %H:%M:%S')
                if time_key not in time_aggregated:
                    time_aggregated[time_key] = {
                        'time': time_key,
                        'values': [],
                        'count': 0
                    }
                time_aggregated[time_key]['values'].append(float(reading.item_value))
                time_aggregated[time_key]['count'] += 1
            
            # 计算平均值
            item_data = []
            for time_key, agg in sorted(time_aggregated.items()):
                avg_value = sum(agg['values']) / len(agg['values'])
                item_data.append({
                    'time': time_key,
                    'value': round(avg_value, 2),
                    'point_count': agg['count']
                })
            
            result_data[item_name] = item_data
        
        return Response.success({
            'time_window': time_window,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'item_names': item_names,
            'area_id': area_id,
            'point_id': point_id,
            'data': result_data
        })

    # ==================== 环境标准管理 ====================

    @staticmethod
    def get_standards(page=1, size=20, item_name=None):
        """获取环境标准列表"""
        query = EnvStandard.query.filter_by(status=1)
        
        if item_name:
            query = query.filter(EnvStandard.item_name.like(f'%{item_name}%'))
        
        pagination = query.order_by(EnvStandard.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        items = [standard.to_dict() for standard in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_all_standards():
        """获取所有环境标准（用于下拉选择）"""
        standards = EnvStandard.query.filter_by(status=1).all()
        return Response.success([s.to_dict() for s in standards])

    @staticmethod
    def get_standard_by_id(standard_id):
        """获取环境标准详情"""
        standard = EnvStandard.get_by_id(standard_id)
        if not standard:
            return Response.not_found('环境标准不存在')
        return Response.success(standard.to_dict())

    @staticmethod
    def create_standard(data):
        """创建环境标准"""
        validation = Validator.validate_form(data, {
            'item_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        
        if EnvStandard.query.filter_by(item_name=data['item_name'], status=1).first():
            return Response.bad_request('该监测项目标准已存在')
        
        standard = EnvStandard(
            item_name=data['item_name'],
            item_unit=data.get('item_unit', ''),
            safety_low=float(data['safety_low']) if data.get('safety_low') else None,
            safety_high=float(data['safety_high']) if data.get('safety_high') else None,
            alert_low=float(data['alert_low']) if data.get('alert_low') else None,
            alert_high=float(data['alert_high']) if data.get('alert_high') else None,
            severity=data.get('severity', 'warning'),
            description=data.get('description', '')
        )
        standard.save()
        
        return Response.success(standard.to_dict(), '环境标准创建成功')

    @staticmethod
    def update_standard(standard_id, data):
        """更新环境标准"""
        standard = EnvStandard.get_by_id(standard_id)
        if not standard:
            return Response.not_found('环境标准不存在')
        
        if 'item_name' in data and data['item_name'] != standard.item_name:
            if EnvStandard.query.filter(EnvStandard.item_name == data['item_name'], EnvStandard.id != standard_id, EnvStandard.status == 1).first():
                return Response.bad_request('该监测项目标准已存在')
        
        standard.update(
            item_name=data.get('item_name', standard.item_name),
            item_unit=data.get('item_unit', standard.item_unit),
            safety_low=float(data['safety_low']) if data.get('safety_low') else standard.safety_low,
            safety_high=float(data['safety_high']) if data.get('safety_high') else standard.safety_high,
            alert_low=float(data['alert_low']) if data.get('alert_low') else standard.alert_low,
            alert_high=float(data['alert_high']) if data.get('alert_high') else standard.alert_high,
            severity=data.get('severity', standard.severity),
            description=data.get('description', standard.description)
        )
        
        return Response.success(standard.to_dict(), '环境标准更新成功')

    @staticmethod
    def delete_standard(standard_id):
        """删除环境标准"""
        standard = EnvStandard.get_by_id(standard_id)
        if not standard:
            return Response.not_found('环境标准不存在')
        
        standard.delete()
        return Response.success(message='环境标准删除成功')

    # ==================== 数据模拟 ====================

    @staticmethod
    def generate_simulated_readings(config=None):
        """
        生成环境监测模拟读数
        config: {
            'interval': 5,  # 分钟
            'abnormal_probability': 0.1  # 异常概率
        }
        """
        if config is None:
            config = {
                'interval': 5,
                'abnormal_probability': 0.1
            }
        
        # 获取所有活跃的监测点
        points = EnvMonitorPoint.query.filter_by(status=1, point_status='active').all()
        
        now = datetime.now()
        generated_count = 0
        
        for point in points:
            monitor_items = point.get_monitor_items()
            for item in monitor_items:
                # 获取标准
                standard = EnvStandard.query.filter_by(item_name=item['name'], status=1).first()
                
                # 生成模拟值
                base_value = EnvMonitorService._get_base_value(item['name'])
                value = base_value + random.uniform(-base_value * 0.1, base_value * 0.1)
                
                # 根据概率生成异常值
                if random.random() < config.get('abnormal_probability', 0.1):
                    if standard:
                        # 生成超出阈值的值
                        if standard.alert_high and random.random() > 0.5:
                            value = float(standard.alert_high) * (1 + random.uniform(0.1, 0.3))
                        elif standard.alert_low:
                            value = float(standard.alert_low) * (1 - random.uniform(0.1, 0.3))
                
                # 创建读数
                reading_data = {
                    'point_id': point.id,
                    'item_name': item['name'],
                    'item_value': round(value, 2),
                    'item_unit': item['unit'],
                    'read_time': now
                }
                EnvMonitorService.add_reading(reading_data)
                generated_count += 1
        
        return Response.success({
            'generated_count': generated_count,
            'point_count': len(points),
            'time': now.strftime('%Y-%m-%d %H:%M:%S')
        }, f'成功生成{generated_count}条模拟读数')

    @staticmethod
    def _get_base_value(item_name):
        """获取监测项目的基准值"""
        base_values = {
            '温度': 25,
            '湿度': 50,
            'PM2.5': 35,
            'PM10': 70,
            '噪音': 60,
            'CO2': 600,
            'CO': 5,
            '甲醛': 0.05,
            'TVOC': 0.3,
            '气压': 1013,
            '风速': 0.5,
            '照度': 500
        }
        return base_values.get(item_name, 50)

    @staticmethod
    def init_default_standards():
        """初始化默认环境标准（仅当不存在时创建）"""
        default_standards = [
            {
                'item_name': '温度',
                'item_unit': '°C',
                'safety_low': 18,
                'safety_high': 26,
                'alert_low': 15,
                'alert_high': 30,
                'severity': 'warning',
                'description': '车间环境温度标准，舒适范围18-26°C'
            },
            {
                'item_name': '湿度',
                'item_unit': '%',
                'safety_low': 40,
                'safety_high': 70,
                'alert_low': 30,
                'alert_high': 80,
                'severity': 'warning',
                'description': '车间环境相对湿度标准，舒适范围40-70%'
            },
            {
                'item_name': 'PM2.5',
                'item_unit': 'μg/m³',
                'safety_low': None,
                'safety_high': 35,
                'alert_low': None,
                'alert_high': 75,
                'severity': 'error',
                'description': '细颗粒物浓度，日均值标准≤35μg/m³为优'
            },
            {
                'item_name': 'PM10',
                'item_unit': 'μg/m³',
                'safety_low': None,
                'safety_high': 70,
                'alert_low': None,
                'alert_high': 150,
                'severity': 'warning',
                'description': '可吸入颗粒物浓度，日均值标准≤70μg/m³为优'
            },
            {
                'item_name': '噪音',
                'item_unit': 'dB',
                'safety_low': None,
                'safety_high': 70,
                'alert_low': None,
                'alert_high': 85,
                'severity': 'error',
                'description': '工作场所噪音标准，85dB以上需佩戴听力防护'
            },
            {
                'item_name': 'CO2',
                'item_unit': 'ppm',
                'safety_low': None,
                'safety_high': 1000,
                'alert_low': None,
                'alert_high': 5000,
                'severity': 'warning',
                'description': '二氧化碳浓度，室内空气质量标准≤1000ppm'
            },
            {
                'item_name': 'CO',
                'item_unit': 'ppm',
                'safety_low': None,
                'safety_high': 25,
                'alert_low': None,
                'alert_high': 100,
                'severity': 'critical',
                'description': '一氧化碳浓度，8小时平均允许浓度25ppm'
            },
            {
                'item_name': '甲醛',
                'item_unit': 'mg/m³',
                'safety_low': None,
                'safety_high': 0.1,
                'alert_low': None,
                'alert_high': 0.5,
                'severity': 'error',
                'description': '甲醛浓度，室内空气质量标准≤0.1mg/m³'
            },
            {
                'item_name': 'TVOC',
                'item_unit': 'mg/m³',
                'safety_low': None,
                'safety_high': 0.6,
                'alert_low': None,
                'alert_high': 3.0,
                'severity': 'warning',
                'description': '总挥发性有机物，室内空气质量标准≤0.6mg/m³'
            }
        ]
        
        created_count = 0
        for standard_data in default_standards:
            existing = EnvStandard.query.filter_by(
                item_name=standard_data['item_name'],
                status=1
            ).first()
            if not existing:
                standard = EnvStandard(**standard_data)
                standard.save()
                created_count += 1
        
        return Response.success({
            'created_count': created_count,
            'total_defaults': len(default_standards)
        }, f'初始化完成，创建了{created_count}条默认标准')

    @staticmethod
    def get_statistics():
        """获取环境监测统计数据"""
        total_areas = EnvArea.query.filter_by(status=1).count()
        total_points = EnvMonitorPoint.query.filter_by(status=1).count()
        active_points = EnvMonitorPoint.query.filter_by(status=1, point_status='active').count()
        total_standards = EnvStandard.query.filter_by(status=1).count()
        
        # 今日异常读数
        today = datetime.now().date()
        today_abnormal = EnvReading.query.filter(
            db.func.date(EnvReading.read_time) == today,
            EnvReading.is_normal == False
        ).count()
        
        # 当前活跃告警
        active_alerts = AlertRecord.query.filter_by(
            alert_type='env_abnormal',
            status='active'
        ).count()
        
        return Response.success({
            'total_areas': total_areas,
            'total_points': total_points,
            'active_points': active_points,
            'total_standards': total_standards,
            'today_abnormal': today_abnormal,
            'active_alerts': active_alerts
        })
