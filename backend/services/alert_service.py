"""
告警服务模块
"""
from datetime import datetime
from database.db import db
from models.production import AlertRecord, Equipment, Sensor
from utils.response import Response


class AlertService:
    """告警服务类"""

    @staticmethod
    def get_alerts(page=1, size=10, severity=None, status=None, equipment_id=None):
        """获取告警列表"""
        query = AlertRecord.query

        if severity:
            query = query.filter(AlertRecord.severity == severity)
        if status:
            query = query.filter(AlertRecord.status == status)
        if equipment_id:
            query = query.filter(AlertRecord.equipment_id == equipment_id)

        pagination = query.order_by(AlertRecord.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = []
        for alert in pagination.items:
            try:
                alert_dict = alert.to_dict() if hasattr(alert, 'to_dict') else {}
                # 获取关联设备信息
                if alert.equipment_id:
                    try:
                        equipment = Equipment.get_by_id(alert.equipment_id)
                        if equipment:
                            alert_dict['equipment_name'] = equipment.equipment_name
                            alert_dict['equipment_code'] = equipment.equipment_code
                    except Exception as e:
                        print(f"Error getting equipment {alert.equipment_id}: {e}")
                # 获取关联传感器信息
                if alert.sensor_id:
                    try:
                        sensor = Sensor.get_by_id(alert.sensor_id)
                        if sensor:
                            alert_dict['sensor_name'] = sensor.sensor_name
                    except Exception as e:
                        print(f"Error getting sensor {alert.sensor_id}: {e}")
                items.append(alert_dict)
            except Exception as e:
                print(f"Error processing alert {alert.id}: {e}")
                # 添加一个基本的告警字典
                items.append({
                    'id': alert.id,
                    'alert_code': getattr(alert, 'alert_code', f'ALERT-{alert.id}'),
                    'alert_type': getattr(alert, 'alert_type', 'unknown'),
                    'message': getattr(alert, 'message', ''),
                    'severity': getattr(alert, 'severity', 'warning'),
                    'status': getattr(alert, 'status', 'active'),
                    'create_time': getattr(alert, 'create_time', '')
                })

        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_alert_by_id(alert_id):
        """获取告警详情"""
        alert = AlertRecord.get_by_id(alert_id)
        if not alert:
            return Response.not_found('告警不存在')

        try:
            alert_dict = alert.to_dict() if hasattr(alert, 'to_dict') else {}
            if alert.equipment_id:
                try:
                    equipment = Equipment.get_by_id(alert.equipment_id)
                    if equipment:
                        alert_dict['equipment_name'] = equipment.equipment_name
                except Exception as e:
                    print(f"Error getting equipment {alert.equipment_id}: {e}")
            if alert.sensor_id:
                try:
                    sensor = Sensor.get_by_id(alert.sensor_id)
                    if sensor:
                        alert_dict['sensor_name'] = sensor.sensor_name
                except Exception as e:
                    print(f"Error getting sensor {alert.sensor_id}: {e}")
        except Exception as e:
            print(f"Error processing alert {alert_id}: {e}")
            # 返回一个基本的告警字典
            alert_dict = {
                'id': alert.id,
                'alert_code': getattr(alert, 'alert_code', f'ALERT-{alert.id}'),
                'alert_type': getattr(alert, 'alert_type', 'unknown'),
                'message': getattr(alert, 'message', ''),
                'severity': getattr(alert, 'severity', 'warning'),
                'status': getattr(alert, 'status', 'active'),
                'create_time': getattr(alert, 'create_time', '')
            }

        return Response.success(alert_dict)

    @staticmethod
    def acknowledge_alert(alert_id, note=None):
        """确认告警"""
        alert = AlertRecord.get_by_id(alert_id)
        if not alert:
            return Response.not_found('告警不存在')

        if alert.status != 'active':
            return Response.error('该告警已处理', 400)

        alert.status = 'acknowledged'
        if note:
            alert.resolve_note = note
        alert.update_time = datetime.now()
        db.session.commit()

        return Response.success(alert.to_dict())

    @staticmethod
    def resolve_alert(alert_id, note=None):
        """解决告警"""
        alert = AlertRecord.get_by_id(alert_id)
        if not alert:
            return Response.not_found('告警不存在')

        alert.status = 'resolved'
        alert.resolved_time = datetime.now()
        if note:
            alert.resolve_note = note
        alert.update_time = datetime.now()
        db.session.commit()

        return Response.success(alert.to_dict())

    @staticmethod
    def get_alert_statistics():
        """获取告警统计"""
        total = AlertRecord.query.count()
        active = AlertRecord.query.filter(AlertRecord.status == 'active').count()
        acknowledged = AlertRecord.query.filter(AlertRecord.status == 'acknowledged').count()
        resolved = AlertRecord.query.filter(AlertRecord.status == 'resolved').count()

        # 按严重程度统计
        critical = AlertRecord.query.filter(
            AlertRecord.severity == 'critical',
            AlertRecord.status == 'active'
        ).count()
        error = AlertRecord.query.filter(
            AlertRecord.severity == 'error',
            AlertRecord.status == 'active'
        ).count()
        warning = AlertRecord.query.filter(
            AlertRecord.severity == 'warning',
            AlertRecord.status == 'active'
        ).count()
        info = AlertRecord.query.filter(
            AlertRecord.severity == 'info',
            AlertRecord.status == 'active'
        ).count()

        return Response.success({
            'total': total,
            'active': active,
            'acknowledged': acknowledged,
            'resolved': resolved,
            'by_severity': {
                'critical': critical,
                'error': error,
                'warning': warning,
                'info': info
            }
        })

    @staticmethod
    def create_alert(data):
        """创建告警（手动或自动）"""
        from utils.validator import Validator

        validation = Validator.validate_form(data, {
            'alert_type': ['required'],
            'message': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        # 生成告警编号
        now = datetime.now()
        alert_code = f"ALERT-{now.strftime('%Y%m%d%H%M%S')}-{AlertRecord.query.count() + 1}"

        alert = AlertRecord(
            alert_code=alert_code,
            alert_type=data.get('alert_type'),
            equipment_id=data.get('equipment_id'),
            sensor_id=data.get('sensor_id'),
            severity=data.get('severity', 'warning'),
            message=data.get('message'),
            value=data.get('value'),
            threshold=data.get('threshold'),
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        return Response.success(alert.to_dict())

    @staticmethod
    def batch_resolve(alert_ids, note=None):
        """批量解决告警"""
        resolved_count = 0
        for alert_id in alert_ids:
            alert = AlertRecord.get_by_id(alert_id)
            if alert and alert.status != 'resolved':
                alert.status = 'resolved'
                alert.resolved_time = datetime.now()
                if note:
                    alert.resolve_note = note
                alert.update_time = datetime.now()
                resolved_count += 1

        db.session.commit()
        return Response.success({'resolved_count': resolved_count})
