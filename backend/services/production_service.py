"""
生产线监控服务
"""
from flask import g
from datetime import datetime, timedelta
from database.db import db
from models.production import ProductionLine, Equipment, Sensor, ProductionTask, ProductionRecord, AlertRecord
from models.log import Log
from utils.response import Response
from utils.validator import Validator


class ProductionService:
    """生产线服务类"""

    @staticmethod
    def get_lines(page=1, size=10, status=None):
        """获取生产线列表"""
        # 生产线的status字段是业务状态(running/stopped/maintenance/error)
        # 不是BaseModel的逻辑删除标记(0/1)
        # 因此这里不过滤逻辑删除状态
        query = ProductionLine.query

        # 业务状态过滤
        if status:
            query = query.filter(ProductionLine.status == status)

        pagination = query.order_by(ProductionLine.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = []
        for line in pagination.items:
            line_dict = line.to_dict()
            line_dict['equipment_count'] = line.equipments.count()
            line_dict['running_count'] = line.equipments.filter_by(status='running').count()
            items.append(line_dict)

        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_line_by_id(line_id):
        """获取生产线详情"""
        # 生产线的status字段是业务状态(running/stopped/maintenance/error)
        # 不是BaseModel的逻辑删除标记
        line = ProductionLine.query.filter(
            ProductionLine.id == line_id
        ).first()

        if not line:
            return Response.not_found('生产线不存在')

        line_dict = line.to_dict()
        line_dict['equipments'] = [e.to_dict() for e in line.equipments.all()]
        line_dict['tasks'] = [t.to_dict() for t in line.tasks.filter(
            ProductionTask.status == 'in_progress'
        ).limit(5).all()]

        return Response.success(line_dict)

    @staticmethod
    def create_line(data):
        """创建生产线"""
        validation = Validator.validate_form(data, {
            'line_code': ['required'],
            'line_name': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        # 检查编号是否存在
        if ProductionLine.query.filter_by(line_code=data['line_code']).first():
            return Response.error('生产线编号已存在', 409)

        line = ProductionLine(
            line_code=data['line_code'],
            line_name=data['line_name'],
            description=data.get('description'),
            capacity=data.get('capacity', 0),
            location=data.get('location'),
            supervisor=data.get('supervisor'),
            status='stopped'
        )

        try:
            line.save()
            Log.add_log(g.user_id, g.username, 'create', 'production_line',
                       f'创建生产线: {line.line_name}')
            return Response.created({'id': line.id}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_line(line_id, data):
        """更新生产线"""
        line = ProductionLine.get_by_id(line_id)
        if not line:
            return Response.not_found('生产线不存在')

        allowed = ['line_name', 'description', 'capacity', 'location', 'supervisor', 'status']
        update_data = {k: v for k, v in data.items() if k in allowed}

        line.update(**update_data)

        Log.add_log(g.user_id, g.username, 'update', 'production_line',
                   f'更新生产线: {line.line_name}')

        return Response.success(line.to_dict(), '更新成功')

    @staticmethod
    def delete_line(line_id):
        """删除生产线"""
        line = ProductionLine.get_by_id(line_id)
        if not line:
            return Response.not_found('生产线不存在')

        line.delete()
        Log.add_log(g.user_id, g.username, 'delete', 'production_line',
                   f'删除生产线: {line.line_name}')

        return Response.success(message='删除成功')


class EquipmentService:
    """设备服务类"""

    @staticmethod
    def get_equipments(page=1, size=10, line_id=None, status=None):
        """获取设备列表"""
        # 设备的status字段是业务状态(running/idle/maintenance/error/offline)
        # 不是BaseModel的逻辑删除标记(0/1)
        # 因此这里不过滤逻辑删除状态
        query = Equipment.query

        if line_id:
            query = query.filter(Equipment.line_id == line_id)
        if status:
            query = query.filter(Equipment.status == status)

        pagination = query.order_by(Equipment.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [e.to_dict() for e in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_equipment_by_id(equipment_id):
        """获取设备详情"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return Response.not_found('设备不存在')

        eq_dict = equipment.to_dict()
        eq_dict['sensors'] = [s.to_dict() for s in equipment.sensors.all()]

        return Response.success(eq_dict)

    @staticmethod
    def create_equipment(data):
        """创建设备"""
        validation = Validator.validate_form(data, {
            'equipment_code': ['required'],
            'equipment_name': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        if Equipment.query.filter_by(equipment_code=data['equipment_code']).first():
            return Response.error('设备编号已存在', 409)

        equipment = Equipment(
            equipment_code=data['equipment_code'],
            equipment_name=data['equipment_name'],
            equipment_type=data.get('equipment_type'),
            line_id=data.get('line_id'),
            model=data.get('model'),
            manufacturer=data.get('manufacturer'),
            status='offline'
        )

        try:
            equipment.save()
            Log.add_log(g.user_id, g.username, 'create', 'equipment',
                       f'创建设备: {equipment.equipment_name}')
            return Response.created({'id': equipment.id}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_equipment(equipment_id, data):
        """更新设备"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return Response.not_found('设备不存在')

        allowed = ['equipment_name', 'equipment_type', 'line_id', 'model',
                  'manufacturer', 'status', 'temperature', 'pressure', 'speed']
        update_data = {k: v for k, v in data.items() if k in allowed}

        equipment.update(**update_data)
        Log.add_log(g.user_id, g.username, 'update', 'equipment',
                   f'更新设备: {equipment.equipment_name}')

        return Response.success(equipment.to_dict(), '更新成功')

    @staticmethod
    def control_equipment(equipment_id, action):
        """控制设备（启动/停止）"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return Response.not_found('设备不存在')

        if action == 'start':
            equipment.status = 'running'
        elif action == 'stop':
            equipment.status = 'idle'
        elif action == 'maintenance':
            equipment.status = 'maintenance'
        else:
            return Response.bad_request('无效的操作')

        equipment.save()
        Log.add_log(g.user_id, g.username, action, 'equipment',
                   f'{action}设备: {equipment.equipment_name}')

        return Response.success(equipment.to_dict(), f'{action}成功')


class SensorService:
    """传感器服务类"""

    @staticmethod
    def get_sensors(equipment_id=None, status=None):
        """获取传感器列表"""
        query = Sensor.query.filter(Sensor.status != 0)

        if equipment_id:
            query = query.filter(Sensor.equipment_id == equipment_id)
        if status:
            query = query.filter(Sensor.status == status)

        sensors = query.order_by(Sensor.create_time.desc()).all()

        return Response.success([s.to_dict() for s in sensors])

    @staticmethod
    def get_sensor_realtime_data(equipment_id=None):
        """获取实时传感器数据（用于图表）"""
        query = Sensor.query.filter(Sensor.status != 0)

        if equipment_id:
            query = query.filter(Sensor.equipment_id == equipment_id)

        sensors = query.all()

        # 按类型分组
        data_by_type = {}
        for sensor in sensors:
            sensor_type = sensor.sensor_type or 'other'
            if sensor_type not in data_by_type:
                data_by_type[sensor_type] = []
            data_by_type[sensor_type].append({
                'id': sensor.id,
                'name': sensor.sensor_name,
                'value': float(sensor.last_value) if sensor.last_value else 0,
                'unit': sensor.unit,
                'status': sensor.status,
                'equipment_id': sensor.equipment_id
            })

        return Response.success(data_by_type)


class TaskService:
    """任务服务类"""

    @staticmethod
    def get_tasks(page=1, size=10, line_id=None, status=None):
        """获取任务列表"""
        query = ProductionTask.query.filter(ProductionTask.status != 0)

        if line_id:
            query = query.filter(ProductionTask.line_id == line_id)
        if status:
            query = query.filter(ProductionTask.status == status)

        pagination = query.order_by(ProductionTask.priority.desc(), ProductionTask.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [t.to_dict() for t in pagination.items]

        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def create_task(data):
        """创建任务"""
        validation = Validator.validate_form(data, {
            'task_code': ['required'],
            'task_name': ['required'],
            'quantity': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        if ProductionTask.query.filter_by(task_code=data['task_code']).first():
            return Response.error('任务编号已存在', 409)

        task = ProductionTask(
            task_code=data['task_code'],
            task_name=data['task_name'],
            line_id=data.get('line_id'),
            product_name=data.get('product_name'),
            product_spec=data.get('product_spec'),
            quantity=data.get('quantity'),
            priority=data.get('priority', 5),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            status='pending'
        )

        try:
            task.save()
            return Response.created({'id': task.id}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_task_status(task_id, new_status):
        """更新任务状态"""
        task = ProductionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('任务不存在')

        # 定义允许的状态转换
        valid_transitions = {
            'pending': ['in_progress', 'cancelled'],
            'in_progress': ['paused', 'completed', 'cancelled'],
            'paused': ['in_progress', 'cancelled'],
            'completed': [],  # 完成状态不能再改变
            'cancelled': []   # 取消状态不能再改变
        }

        current_status = task.status
        allowed_next_states = valid_transitions.get(current_status, [])

        if new_status not in allowed_next_states:
            return Response.error(f'不能从{current_status}状态变更为{new_status}状态', 400)

        # 更新状态
        task.status = new_status

        # 设置时间戳
        from datetime import datetime
        if new_status == 'in_progress' and not task.actual_start_time:
            task.actual_start_time = datetime.now()
        elif new_status == 'completed':
            task.actual_end_time = datetime.now()
        elif new_status == 'cancelled' and not task.actual_end_time:
            task.actual_end_time = datetime.now()

        try:
            task.save()
            Log.add_log(g.user_id, g.username, 'update', 'production_task',
                       f'更新任务状态: {task.task_name} ({current_status} -> {new_status})')
            return Response.success(task.to_dict(), '状态更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'更新失败: {str(e)}')


class StatisticsService:
    """生产线统计服务"""

    @staticmethod
    def get_dashboard_data():
        """获取仪表盘数据"""
        # 生产线统计（status是业务状态，不过滤）
        total_lines = ProductionLine.query.count()
        running_lines = ProductionLine.query.filter(ProductionLine.status == 'running').count()

        # 设备统计（status是业务状态）
        total_equipments = Equipment.query.count()
        running_equipments = Equipment.query.filter(Equipment.status == 'running').count()
        error_equipments = Equipment.query.filter(Equipment.status == 'error').count()

        # 传感器统计（status是业务状态）
        total_sensors = Sensor.query.count()
        normal_sensors = Sensor.query.filter(Sensor.status == 'normal').count()
        warning_sensors = Sensor.query.filter(Sensor.status == 'warning').count()

        # 任务统计
        total_tasks = ProductionTask.query.filter(ProductionTask.status != 0).count()
        in_progress_tasks = ProductionTask.query.filter(ProductionTask.status == 'in_progress').count()
        completed_tasks = ProductionTask.query.filter(ProductionTask.status == 'completed').count()

        # 告警统计
        active_alerts = AlertRecord.query.filter(AlertRecord.status == 'active').count()

        # 今日生产数据
        today = datetime.now().date()
        today_records = ProductionRecord.query.filter(
            db.func.date(ProductionRecord.record_time) == today
        ).all()

        today_products = sum(r.product_count or 0 for r in today_records)
        today_qualified = sum(r.qualified_count or 0 for r in today_records)

        return Response.success({
            'production': {
                'total_lines': total_lines,
                'running_lines': running_lines,
                'total_equipments': total_equipments,
                'running_equipments': running_equipments,
                'error_equipments': error_equipments
            },
            'sensors': {
                'total': total_sensors,
                'normal': normal_sensors,
                'warning': warning_sensors
            },
            'tasks': {
                'total': total_tasks,
                'in_progress': in_progress_tasks,
                'completed': completed_tasks
            },
            'alerts': {
                'active': active_alerts
            },
            'today': {
                'products': today_products,
                'qualified': today_qualified,
                'yield_rate': round(today_qualified / today_products * 100, 2) if today_products > 0 else 0
            }
        })

    @staticmethod
    def get_equipment_trend(days=7):
        """获取设备运行趋势"""
        start_date = datetime.now() - timedelta(days=days)

        records = ProductionRecord.query.filter(
            ProductionRecord.record_time >= start_date
        ).order_by(ProductionRecord.record_time).all()

        # 按日期分组
        trend_data = {}
        for record in records:
            date_key = record.record_time.strftime('%Y-%m-%d')
            if date_key not in trend_data:
                trend_data[date_key] = {'count': 0, 'qualified': 0}
            trend_data[date_key]['count'] += record.product_count or 0
            trend_data[date_key]['qualified'] += record.qualified_count or 0

        labels = list(trend_data.keys())
        values = [trend_data[d]['count'] for d in labels]

        return Response.success({
            'labels': labels,
            'values': values
        })
