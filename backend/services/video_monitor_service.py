"""
视频监控服务模块
"""
from datetime import datetime
from database.db import db
from models.video_monitor import (
    Camera, CameraEquipmentRelation, PatrolGroup,
    PatrolGroupCamera, CaptureRecord
)
from models.production import Equipment
from utils.response import Response


PLACEHOLDER_IMAGE_BASE64 = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NDAiIGhlaWdodD0iMzYwIiB2aWV3Qm94PSIwIDAgNjQwIDM2MCI+"
    "PHJlY3Qgd2lkdGg9IjY0MCIgaGVpZ2h0PSIzNjAiIGZpbGw9IiMxZTM3NDYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjM0IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+56We6aG15a2Q572R5Zu+5LqGPC90ZXh0Pjwvc3ZnPg=="
)


class CameraService:
    """摄像头档案服务"""

    @staticmethod
    def get_cameras(page=1, size=10, keyword=None, online_status=None, line_id=None):
        """获取摄像头列表"""
        query = Camera.query

        if keyword:
            query = query.filter(
                (Camera.camera_code.like(f'%{keyword}%')) |
                (Camera.camera_name.like(f'%{keyword}%')) |
                (Camera.ip_address.like(f'%{keyword}%'))
            )
        if online_status:
            query = query.filter(Camera.online_status == online_status)
        if line_id:
            query = query.filter(Camera.line_id == line_id)

        pagination = query.order_by(Camera.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_all_cameras():
        """获取所有摄像头（不分页）"""
        cameras = Camera.get_all()
        return Response.success([c.to_dict() for c in cameras])

    @staticmethod
    def get_camera_by_id(camera_id):
        """获取摄像头详情"""
        camera = Camera.get_by_id(camera_id)
        if not camera:
            return Response.not_found('摄像头不存在')

        result = camera.to_dict()
        try:
            relations = CameraEquipmentRelation.query.filter_by(
                camera_id=camera_id, status=1
            ).all()
            result['equipments'] = [r.to_dict() for r in relations]
        except Exception:
            result['equipments'] = []

        return Response.success(result)

    @staticmethod
    def create_camera(data):
        """创建摄像头"""
        from utils.validator import Validator

        validation = Validator.validate_form(data, {
            'camera_code': ['required'],
            'camera_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        existing = Camera.query.filter_by(camera_code=data.get('camera_code')).first()
        if existing:
            return Response.bad_request('摄像头编号已存在')

        camera = Camera(
            camera_code=data.get('camera_code'),
            camera_name=data.get('camera_name'),
            ip_address=data.get('ip_address'),
            stream_url=data.get('stream_url'),
            line_id=data.get('line_id'),
            area=data.get('area'),
            online_status=data.get('online_status', 'offline'),
            description=data.get('description')
        )
        camera.save()

        equipment_ids = data.get('equipment_ids', [])
        if equipment_ids:
            for eq_id in equipment_ids:
                relation = CameraEquipmentRelation(
                    camera_id=camera.id,
                    equipment_id=eq_id
                )
                relation.save()

        return Response.success(camera.to_dict())

    @staticmethod
    def update_camera(camera_id, data):
        """更新摄像头"""
        camera = Camera.get_by_id(camera_id)
        if not camera:
            return Response.not_found('摄像头不存在')

        if data.get('camera_code') and data['camera_code'] != camera.camera_code:
            existing = Camera.query.filter_by(camera_code=data['camera_code']).first()
            if existing:
                return Response.bad_request('摄像头编号已存在')

        fields = ['camera_code', 'camera_name', 'ip_address', 'stream_url',
                  'line_id', 'area', 'online_status', 'description']
        for field in fields:
            if field in data:
                setattr(camera, field, data[field])

        camera.update_time = datetime.now()
        db.session.commit()

        if 'equipment_ids' in data:
            CameraEquipmentRelation.query.filter_by(camera_id=camera_id).delete()
            for eq_id in data['equipment_ids']:
                relation = CameraEquipmentRelation(
                    camera_id=camera_id,
                    equipment_id=eq_id
                )
                relation.save()

        return Response.success(camera.to_dict())

    @staticmethod
    def delete_camera(camera_id):
        """删除摄像头"""
        camera = Camera.get_by_id(camera_id)
        if not camera:
            return Response.not_found('摄像头不存在')

        camera.delete()
        return Response.success({'id': camera_id})

    @staticmethod
    def report_heartbeat(camera_code=None, camera_id=None):
        """心跳上报"""
        query = Camera.query
        if camera_id:
            query = query.filter_by(id=camera_id)
        elif camera_code:
            query = query.filter_by(camera_code=camera_code)
        else:
            return Response.bad_request('缺少摄像头标识')

        camera = query.first()
        if not camera:
            return Response.not_found('摄像头不存在')

        camera.online_status = 'online'
        camera.last_heartbeat = datetime.now()
        db.session.commit()

        return Response.success({
            'camera_id': camera.id,
            'camera_code': camera.camera_code,
            'online_status': 'online',
            'last_heartbeat': camera.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
        })


class PatrolGroupService:
    """巡视分组服务"""

    @staticmethod
    def get_groups(page=1, size=10, keyword=None):
        """获取分组列表"""
        query = PatrolGroup.query

        if keyword:
            query = query.filter(PatrolGroup.group_name.like(f'%{keyword}%'))

        pagination = query.order_by(PatrolGroup.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_all_groups():
        """获取所有分组"""
        groups = PatrolGroup.get_all()
        return Response.success([g.to_dict() for g in groups])

    @staticmethod
    def get_group_by_id(group_id):
        """获取分组详情"""
        group = PatrolGroup.get_by_id(group_id)
        if not group:
            return Response.not_found('分组不存在')

        result = group.to_dict()
        try:
            cameras = PatrolGroupCamera.query.filter_by(
                group_id=group_id, status=1
            ).order_by(PatrolGroupCamera.sort_order.asc()).all()
            result['cameras'] = [c.to_dict() for c in cameras]
        except Exception:
            result['cameras'] = []

        return Response.success(result)

    @staticmethod
    def get_group_online_cameras(group_id):
        """按分组获取当前在线摄像头"""
        group = PatrolGroup.get_by_id(group_id)
        if not group:
            return Response.not_found('分组不存在')

        cameras = PatrolGroupCamera.query.filter_by(
            group_id=group_id, status=1
        ).order_by(PatrolGroupCamera.sort_order.asc()).all()

        result = []
        for rel in cameras:
            if rel.camera and rel.camera.online_status == 'online':
                result.append(rel.camera.to_dict())

        return Response.success({
            'group_id': group_id,
            'group_name': group.group_name,
            'layout': group.layout,
            'cameras': result,
            'total_count': len(cameras),
            'online_count': len(result)
        })

    @staticmethod
    def create_group(data):
        """创建分组"""
        from utils.validator import Validator

        validation = Validator.validate_form(data, {
            'group_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        group = PatrolGroup(
            group_name=data.get('group_name'),
            layout=data.get('layout', '4'),
            description=data.get('description')
        )
        group.save()

        camera_ids = data.get('camera_ids', [])
        for idx, cam_id in enumerate(camera_ids):
            rel = PatrolGroupCamera(
                group_id=group.id,
                camera_id=cam_id,
                sort_order=idx
            )
            rel.save()

        return Response.success(group.to_dict())

    @staticmethod
    def update_group(group_id, data):
        """更新分组"""
        group = PatrolGroup.get_by_id(group_id)
        if not group:
            return Response.not_found('分组不存在')

        for field in ['group_name', 'layout', 'description']:
            if field in data:
                setattr(group, field, data[field])

        group.update_time = datetime.now()
        db.session.commit()

        if 'camera_ids' in data:
            PatrolGroupCamera.query.filter_by(group_id=group_id).delete()
            for idx, cam_id in enumerate(data['camera_ids']):
                rel = PatrolGroupCamera(
                    group_id=group_id,
                    camera_id=cam_id,
                    sort_order=idx
                )
                rel.save()

        return Response.success(group.to_dict())

    @staticmethod
    def delete_group(group_id):
        """删除分组"""
        group = PatrolGroup.get_by_id(group_id)
        if not group:
            return Response.not_found('分组不存在')

        group.delete()
        return Response.success({'id': group_id})


class CaptureRecordService:
    """抓图记录服务"""

    @staticmethod
    def get_records(page=1, size=10, source=None, camera_id=None, alert_id=None,
                    start_time=None, end_time=None):
        """获取抓图记录列表"""
        query = CaptureRecord.query

        if source:
            query = query.filter(CaptureRecord.source == source)
        if camera_id:
            query = query.filter(CaptureRecord.camera_id == camera_id)
        if alert_id:
            query = query.filter(CaptureRecord.alert_id == alert_id)
        if start_time:
            query = query.filter(CaptureRecord.trigger_time >= start_time)
        if end_time:
            query = query.filter(CaptureRecord.trigger_time <= end_time)

        pagination = query.order_by(CaptureRecord.trigger_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_records_by_alert(alert_id):
        """根据告警ID获取抓图记录"""
        records = CaptureRecord.query.filter_by(
            alert_id=alert_id
        ).order_by(CaptureRecord.trigger_time.desc()).all()

        return Response.success([r.to_dict() for r in records])

    @staticmethod
    def create_manual_capture(camera_id):
        """手动抓图"""
        camera = Camera.get_by_id(camera_id)
        if not camera:
            return Response.not_found('摄像头不存在')

        record = CaptureRecord(
            camera_id=camera_id,
            source='manual',
            trigger_time=datetime.now(),
            image_base64=PLACEHOLDER_IMAGE_BASE64
        )
        record.save()

        return Response.success(record.to_dict())

    @staticmethod
    def create_alert_capture(alert_id, equipment_id=None):
        """告警自动抓图（告警发生时调用）"""
        from models.production import AlertRecord

        alert = AlertRecord.query.filter_by(id=alert_id).first()
        if not alert:
            return Response.not_found('告警不存在')

        query = CameraEquipmentRelation.query.filter_by(status=1)
        if equipment_id:
            query = query.filter_by(equipment_id=equipment_id)
        elif alert.equipment_id:
            query = query.filter_by(equipment_id=alert.equipment_id)

        relations = query.all()
        camera_ids = list(set([r.camera_id for r in relations]))

        if not camera_ids:
            return Response.success({'created_count': 0, 'message': '未找到关联摄像头'})

        created = []
        for cam_id in camera_ids:
            camera = Camera.get_by_id(cam_id)
            if camera:
                record = CaptureRecord(
                    camera_id=cam_id,
                    source='alert_auto',
                    trigger_time=datetime.now(),
                    alert_id=alert_id,
                    image_base64=PLACEHOLDER_IMAGE_BASE64
                )
                record.save()
                created.append(record.to_dict())

        return Response.success({
            'created_count': len(created),
            'records': created
        })

    @staticmethod
    def get_record_by_id(record_id):
        """获取抓图记录详情"""
        record = CaptureRecord.query.filter_by(id=record_id).first()
        if not record:
            return Response.not_found('抓图记录不存在')
        return Response.success(record.to_dict())
