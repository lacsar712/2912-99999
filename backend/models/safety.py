"""
安全管理模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class HazardType(BaseModel):
    """隐患类型字典"""
    __tablename__ = 'hazard_type'

    type_code = db.Column(db.String(50), unique=True, nullable=False, comment='类型编码')
    type_name = db.Column(db.String(100), nullable=False, comment='类型名称')
    category = db.Column(db.String(50), comment='分类(人员违规/设备隐患/环境隐患/消防隐患)')
    description = db.Column(db.Text, comment='描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    def __repr__(self):
        return f'<HazardType {self.type_name}>'


class InspectionTask(BaseModel):
    """隐患排查任务"""
    __tablename__ = 'inspection_task'

    task_code = db.Column(db.String(50), unique=True, nullable=False, comment='任务编号')
    task_name = db.Column(db.String(100), nullable=False, comment='任务名称')
    task_type = db.Column(db.Enum('plan', 'periodic', 'temporary'), default='plan', comment='任务类型')
    period = db.Column(db.String(50), comment='周期(daily/weekly/monthly/quarterly)')
    responsible_person = db.Column(db.String(50), comment='负责人')
    area = db.Column(db.String(200), comment='覆盖区域')
    description = db.Column(db.Text, comment='任务描述')
    next_execution = db.Column(db.DateTime, comment='下次执行时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    def __repr__(self):
        return f'<InspectionTask {self.task_name}>'


class HazardRecord(BaseModel):
    """隐患记录"""
    __tablename__ = 'hazard_record'

    hazard_code = db.Column(db.String(50), unique=True, nullable=False, comment='隐患编号')
    title = db.Column(db.String(200), nullable=False, comment='隐患标题')
    discoverer = db.Column(db.String(50), comment='发现人')
    location = db.Column(db.String(200), comment='地点/设备')
    hazard_type_id = db.Column(db.BigInteger, db.ForeignKey('hazard_type.id'), comment='隐患类型ID')
    severity = db.Column(db.Enum('low', 'medium', 'high', 'critical'), default='medium', comment='严重程度')
    photo_base64 = db.Column(db.Text, comment='现场照片(base64)')
    hazard_status = db.Column(
        db.Enum('pending', 'rectifying', 'rectified', 'accepted'),
        default='pending',
        comment='状态: 待整改/整改中/已整改/已验收'
    )
    description = db.Column(db.Text, comment='隐患描述')
    deadline = db.Column(db.DateTime, comment='整改截止时间')
    is_escalated = db.Column(db.Boolean, default=False, comment='是否已升级')
    inspection_task_id = db.Column(db.BigInteger, db.ForeignKey('inspection_task.id'), comment='关联排查任务ID')

    hazard_type = db.relationship('HazardType', backref='hazard_records', lazy='joined')
    inspection_task = db.relationship('InspectionTask', backref='hazard_records', lazy='joined')
    rectifications = db.relationship('RectificationRecord', backref='hazard_record', lazy='dynamic',
                                     order_by='RectificationRecord.create_time.desc()')

    def to_dict(self):
        result = super().to_dict()
        if self.hazard_type:
            result['hazard_type_name'] = self.hazard_type.type_name
            result['hazard_type_category'] = self.hazard_type.category
        if self.inspection_task:
            result['inspection_task_name'] = self.inspection_task.task_name
        result['rectification_count'] = self.rectifications.count()
        return result

    def __repr__(self):
        return f'<HazardRecord {self.hazard_code}>'


class RectificationRecord(BaseModel):
    """整改记录"""
    __tablename__ = 'rectification_record'

    hazard_id = db.Column(db.BigInteger, db.ForeignKey('hazard_record.id'), nullable=False, comment='隐患记录ID')
    measure = db.Column(db.Text, nullable=False, comment='整改措施描述')
    responsible_person = db.Column(db.String(50), comment='整改责任人')
    plan_complete_time = db.Column(db.DateTime, comment='计划完成时间')
    actual_complete_time = db.Column(db.DateTime, comment='实际完成时间')
    result = db.Column(db.Text, comment='整改结果')
    photo_base64 = db.Column(db.Text, comment='整改后照片(base64)')

    def __repr__(self):
        return f'<RectificationRecord {self.id}>'


class AccidentRecord(BaseModel):
    """事故登记"""
    __tablename__ = 'accident_record'

    accident_code = db.Column(db.String(50), unique=True, nullable=False, comment='事故编号')
    accident_time = db.Column(db.DateTime, nullable=False, comment='事故时间')
    location = db.Column(db.String(200), comment='事故地点')
    involved_persons = db.Column(db.String(500), comment='涉及人员')
    loss_estimate = db.Column(db.Numeric(12, 2), comment='损失估计(元)')
    cause_analysis = db.Column(db.Text, comment='原因分析')
    rectification_measures = db.Column(db.Text, comment='整改措施')
    attachment_base64 = db.Column(db.Text, comment='附件(base64)')
    severity = db.Column(db.Enum('minor', 'general', 'major', 'critical'), default='general', comment='事故等级')
    description = db.Column(db.Text, comment='事故描述')

    def __repr__(self):
        return f'<AccidentRecord {self.accident_code}>'
