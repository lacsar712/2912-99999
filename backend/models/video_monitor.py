"""
视频监控模型
"""
from database.db import db
from models.base import BaseModel


class Camera(BaseModel):
    """摄像头档案模型"""
    __tablename__ = 'camera'

    camera_code = db.Column(db.String(50), unique=True, nullable=False, comment='摄像头编号')
    camera_name = db.Column(db.String(100), nullable=False, comment='摄像头名称')
    ip_address = db.Column(db.String(50), comment='IP地址')
    stream_url = db.Column(db.String(500), comment='流地址(RTSP/HTTP)')
    line_id = db.Column(db.BigInteger, db.ForeignKey('production_line.id'), comment='所属生产线ID')
    area = db.Column(db.String(100), comment='所属区域')
    online_status = db.Column(db.Enum('online', 'offline'), default='offline', comment='在线状态: online在线/offline离线')
    last_heartbeat = db.Column(db.DateTime, comment='最后心跳时间')
    description = db.Column(db.Text, comment='描述')

    equipment_relations = db.relationship(
        'CameraEquipmentRelation',
        backref='camera',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    group_relations = db.relationship(
        'PatrolGroupCamera',
        backref='camera',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    capture_records = db.relationship(
        'CaptureRecord',
        backref='camera',
        lazy='dynamic'
    )

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.line_id:
                from models.production import ProductionLine
                line = ProductionLine.get_by_id(self.line_id)
                if line:
                    result['line_name'] = line.line_name
        except Exception:
            pass
        try:
            result['equipment_count'] = self.equipment_relations.count()
        except Exception:
            result['equipment_count'] = 0
        return result


class CameraEquipmentRelation(BaseModel):
    """设备与摄像头关联模型（一摄像头可关联多设备）"""
    __tablename__ = 'camera_equipment_relation'

    camera_id = db.Column(db.BigInteger, db.ForeignKey('camera.id'), nullable=False, comment='摄像头ID')
    equipment_id = db.Column(db.BigInteger, db.ForeignKey('equipment.id'), nullable=False, comment='设备ID')

    __table_args__ = (
        db.UniqueConstraint('camera_id', 'equipment_id', name='uk_camera_equipment'),
    )

    def to_dict(self):
        result = super().to_dict()
        try:
            from models.production import Equipment
            equipment = Equipment.get_by_id(self.equipment_id)
            if equipment:
                result['equipment_code'] = equipment.equipment_code
                result['equipment_name'] = equipment.equipment_name
        except Exception:
            pass
        return result


class PatrolGroup(BaseModel):
    """巡视分组模型"""
    __tablename__ = 'patrol_group'

    group_name = db.Column(db.String(100), nullable=False, comment='分组名称')
    layout = db.Column(db.Enum('1', '4', '9'), default='4', comment='推荐布局: 1/4/9宫格')
    description = db.Column(db.Text, comment='描述')

    camera_relations = db.relationship(
        'PatrolGroupCamera',
        backref='group',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        result = super().to_dict()
        try:
            result['camera_count'] = self.camera_relations.count()
        except Exception:
            result['camera_count'] = 0
        return result


class PatrolGroupCamera(BaseModel):
    """巡视分组-摄像头关联模型"""
    __tablename__ = 'patrol_group_camera'

    group_id = db.Column(db.BigInteger, db.ForeignKey('patrol_group.id'), nullable=False, comment='分组ID')
    camera_id = db.Column(db.BigInteger, db.ForeignKey('camera.id'), nullable=False, comment='摄像头ID')
    sort_order = db.Column(db.Integer, default=0, comment='排序')

    __table_args__ = (
        db.UniqueConstraint('group_id', 'camera_id', name='uk_group_camera'),
    )

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.camera:
                camera_dict = self.camera.to_dict()
                result.update(camera_dict)
        except Exception:
            pass
        return result


class CaptureRecord(BaseModel):
    """抓图记录模型"""
    __tablename__ = 'capture_record'

    camera_id = db.Column(db.BigInteger, db.ForeignKey('camera.id'), comment='摄像头ID')
    source = db.Column(db.Enum('manual', 'alert_auto'), default='manual', comment='来源: manual手动/alert_auto告警自动')
    trigger_time = db.Column(db.DateTime, comment='触发时间')
    alert_id = db.Column(db.BigInteger, comment='关联告警ID')
    image_base64 = db.Column(db.Text, comment='图片Base64')

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.camera:
                result['camera_code'] = self.camera.camera_code
                result['camera_name'] = self.camera.camera_name
        except Exception:
            pass
        return result
