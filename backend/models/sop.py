"""
SOP标准作业管理模型
"""
import json
from datetime import datetime
from database.db import db
from models.base import BaseModel


class SOPDocument(BaseModel):
    """SOP文档"""
    __tablename__ = 'sop_document'

    sop_code = db.Column(db.String(50), unique=True, nullable=False, comment='SOP编号')
    sop_name = db.Column(db.String(200), nullable=False, comment='SOP名称')
    applicable_product = db.Column(db.String(200), comment='适用产品/工序')
    version = db.Column(db.String(20), default='1.0', comment='版本号')
    sop_status = db.Column(
        db.Enum('draft', 'published', 'deprecated'),
        default='draft',
        comment='状态: 草稿/发布/废弃'
    )
    description = db.Column(db.Text, comment='SOP描述')
    equipment_ids = db.Column(db.Text, comment='关联设备ID列表(逗号分隔)')
    created_by = db.Column(db.BigInteger, comment='创建人ID')

    steps = db.relationship('SOPStep', backref='sop', lazy='dynamic',
                            cascade='all, delete-orphan', order_by='SOPStep.step_order')
    versions = db.relationship('SOPVersion', backref='sop', lazy='dynamic',
                               cascade='all, delete-orphan')
    checklists = db.relationship('SOPChecklist', backref='sop', lazy='dynamic')

    def get_equipment_ids(self):
        if not self.equipment_ids:
            return []
        return [int(x.strip()) for x in self.equipment_ids.split(',') if x.strip()]

    def set_equipment_ids(self, ids):
        if ids:
            self.equipment_ids = ','.join(str(x) for x in ids)
        else:
            self.equipment_ids = None

    def to_dict(self, include_steps=True):
        result = super().to_dict()
        result.pop('status', None)
        result['status'] = self.sop_status
        result['equipment_id_list'] = self.get_equipment_ids()
        result['step_count'] = self.steps.count()
        if include_steps:
            result['steps'] = [s.to_dict() for s in self.steps.all()]
        return result

    def snapshot_dict(self):
        return {
            'sop_code': self.sop_code,
            'sop_name': self.sop_name,
            'applicable_product': self.applicable_product,
            'version': self.version,
            'description': self.description,
            'equipment_ids': self.equipment_ids,
            'steps': [s.snapshot_dict() for s in self.steps.all()]
        }

    def __repr__(self):
        return f'<SOPDocument {self.sop_code} v{self.version}>'


class SOPStep(BaseModel):
    """SOP步骤"""
    __tablename__ = 'sop_step'

    sop_id = db.Column(db.BigInteger, db.ForeignKey('sop_document.id'), nullable=False, comment='SOP ID')
    step_order = db.Column(db.Integer, default=1, comment='步骤顺序')
    title = db.Column(db.String(200), nullable=False, comment='步骤标题')
    description = db.Column(db.Text, comment='步骤描述')
    image_base64 = db.Column(db.Text, comment='步骤图片(base64)')
    video_url = db.Column(db.String(500), comment='视频URL')
    duration_minutes = db.Column(db.Integer, default=0, comment='预计时长(分钟)')

    def to_dict(self):
        result = super().to_dict()
        return result

    def snapshot_dict(self):
        return {
            'step_order': self.step_order,
            'title': self.title,
            'description': self.description,
            'video_url': self.video_url,
            'duration_minutes': self.duration_minutes,
            'has_image': bool(self.image_base64)
        }

    def __repr__(self):
        return f'<SOPStep SOP={self.sop_id} Order={self.step_order}>'


class SOPVersion(BaseModel):
    """SOP版本记录"""
    __tablename__ = 'sop_version'

    sop_id = db.Column(db.BigInteger, db.ForeignKey('sop_document.id'), nullable=False, comment='SOP ID')
    version = db.Column(db.String(20), nullable=False, comment='版本号')
    change_log = db.Column(db.Text, comment='变更说明')
    content_snapshot = db.Column(db.Text, comment='内容快照(JSON)')
    published_by = db.Column(db.BigInteger, comment='发布人ID')
    published_time = db.Column(db.DateTime, default=datetime.now, comment='发布时间')

    def get_snapshot(self):
        if not self.content_snapshot:
            return {}
        try:
            return json.loads(self.content_snapshot)
        except Exception:
            return {}

    def set_snapshot(self, data):
        self.content_snapshot = json.dumps(data, ensure_ascii=False)

    def to_dict(self):
        result = super().to_dict()
        result['snapshot'] = self.get_snapshot()
        return result

    def __repr__(self):
        return f'<SOPVersion SOP={self.sop_id} v{self.version}>'


class SOPTrainingRelation(BaseModel):
    """SOP与培训课程关联"""
    __tablename__ = 'sop_training_relation'

    sop_id = db.Column(db.BigInteger, db.ForeignKey('sop_document.id'), nullable=False, comment='SOP ID')
    training_course_id = db.Column(db.BigInteger, db.ForeignKey('training_course.id'), nullable=False, comment='培训课程ID')

    __table_args__ = (
        db.UniqueConstraint('sop_id', 'training_course_id', name='uk_sop_training'),
    )

    def to_dict(self):
        result = super().to_dict()
        try:
            from models.training import TrainingCourse
            course = TrainingCourse.get_by_id(self.training_course_id)
            if course:
                result['course_code'] = course.course_code
                result['course_name'] = course.course_name
        except Exception:
            pass
        return result

    def __repr__(self):
        return f'<SOPTrainingRelation SOP={self.sop_id} Course={self.training_course_id}>'


class SOPChecklist(BaseModel):
    """SOP执行检查表"""
    __tablename__ = 'sop_checklist'

    sop_id = db.Column(db.BigInteger, db.ForeignKey('sop_document.id'), nullable=False, comment='SOP ID')
    sop_version = db.Column(db.String(20), comment='执行时SOP版本')
    equipment_id = db.Column(db.BigInteger, comment='执行设备ID')
    operator_id = db.Column(db.BigInteger, comment='操作员ID')
    operator_name = db.Column(db.String(100), comment='操作员姓名')
    start_time = db.Column(db.DateTime, default=datetime.now, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='完成时间')
    compliance_rate = db.Column(db.Numeric(5, 2), default=0, comment='合规率(%)')
    signer_id = db.Column(db.BigInteger, comment='签到人ID')
    signer_name = db.Column(db.String(100), comment='签到人姓名')
    sign_time = db.Column(db.DateTime, comment='签到时间')
    remark = db.Column(db.Text, comment='备注')

    items = db.relationship('SOPChecklistItem', backref='checklist', lazy='dynamic',
                            cascade='all, delete-orphan')

    def to_dict(self, include_items=True):
        result = super().to_dict()
        try:
            sop = SOPDocument.get_by_id(self.sop_id)
            if sop:
                result['sop_code'] = sop.sop_code
                result['sop_name'] = sop.sop_name
        except Exception:
            pass
        try:
            from models.production import Equipment
            if self.equipment_id:
                eq = Equipment.get_by_id(self.equipment_id)
                if eq:
                    result['equipment_code'] = eq.equipment_code
                    result['equipment_name'] = eq.equipment_name
        except Exception:
            pass
        if include_items:
            result['items'] = [i.to_dict() for i in self.items.all()]
        return result

    def calculate_compliance(self):
        items = self.items.all()
        if not items:
            return 0
        total = len(items)
        completed = sum(1 for i in items if i.is_completed)
        return round(completed / total * 100, 2)

    def __repr__(self):
        return f'<SOPChecklist SOP={self.sop_id}>'


class SOPChecklistItem(BaseModel):
    """检查表步骤项"""
    __tablename__ = 'sop_checklist_item'

    checklist_id = db.Column(db.BigInteger, db.ForeignKey('sop_checklist.id'), nullable=False, comment='检查表ID')
    step_order = db.Column(db.Integer, comment='步骤顺序')
    step_title = db.Column(db.String(200), comment='步骤标题')
    step_description = db.Column(db.Text, comment='步骤描述')
    is_completed = db.Column(db.Boolean, default=False, comment='是否完成')
    photo_base64 = db.Column(db.Text, comment='现场照片(base64)')
    remark = db.Column(db.Text, comment='备注')
    completed_time = db.Column(db.DateTime, comment='完成时间')

    def to_dict(self):
        result = super().to_dict()
        return result

    def __repr__(self):
        return f'<SOPChecklistItem Checklist={self.checklist_id} Order={self.step_order}>'
